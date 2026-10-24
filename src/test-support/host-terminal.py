"""Credential-free acceptance driver for the pinned disposable OpenCode host.

Run only through docs/operations/prepare-host.ps1. No prompt/model calls.
Frames/raw terminal output are bounded private evidence, not golden snapshots.
"""
import codecs
import json
import os
from pathlib import Path
import pty
import re
import select
import signal
import subprocess
import termios
import time

import pyte


EVIDENCE = Path('/evidence')
RESULTS = []

# Test-only observer: uses pinned public client/router/keymap/renderer contracts.
# Does not register a server endpoint, seed accounting, or replace any UI slot.
OBSERVER = r'''
import { Plugin } from "/opt/candidate/node_modules/@opencode/plugin/dist/tui/index.js";
import { CostRpc } from "/opt/candidate/dist/rpc.js";
import fs from "node:fs";
export default Plugin.define({id:"cmon-acceptance-observer",setup(ctx) {
  let sessionID;
  let alive = true;
  const generations = "/work/observer-generations.txt";
  fs.appendFileSync(generations, "setup\n");
  ctx.keymap.layer(() => ({commands:[
    {id:"acceptance.session",bind:"f6",run:async()=>{
      if (!sessionID) sessionID = (await ctx.client.session.create({title:"Empty acceptance session"})).id;
      ctx.ui.router.navigate({type:"session",sessionID});
    }},
    {id:"acceptance.home",bind:"f7",run:()=>ctx.ui.router.navigate({type:"home"})},
    {id:"acceptance.reload",bind:"f8",run:()=>ctx.keymap.dispatch("location.reload")},
  ]}));
  const snapshot = async () => {
    try {
      const now = new Date();
      const from = new Date(now.getFullYear(), now.getMonth(), 1).getTime();
      const to = new Date(now.getFullYear(), now.getMonth()+1, 1).getTime();
      const reply = await ctx.client.rpc(CostRpc).summary({from,to});
      const walk = (node, depth=0) => depth > 25 ? null : ({
        id:node.id,x:node.x,y:node.y,width:node.width,height:node.height,
        text:typeof node.content === "string" ? node.content : node.content?.chunks?.map(c=>c.text).join(""),
        children:node.getChildren().map(n=>walk(n,depth+1))
      });
      if (alive) fs.writeFileSync("/work/observer.json",JSON.stringify({reply,route:ctx.ui.router.current(),tree:walk(ctx.renderer.root)}));
    } catch (e) { if (alive) fs.writeFileSync("/work/observer-error.txt",String(e)); }
  };
  const timer = setInterval(snapshot,500);
  return () => {alive=false;clearInterval(timer);fs.appendFileSync(generations,"dispose\n");};
}});
'''

# Compatibility data are deliberately synthetic; this is real schema/transport
# proof, not recording/provider proof. No candidate application changes.
COMPAT_SERVER = r'''
import { Plugin } from "/opt/candidate/node_modules/@opencode/plugin/dist/promise/index.js";
import { CostRpc } from "/opt/candidate/dist/rpc.js";
import fs from "node:fs";
export default Plugin.define({id:"cmon-compatibility-fixture",async setup(ctx) {
  const reply = JSON.parse(fs.readFileSync(new URL("./reply.json",import.meta.url),"utf8"));
  const registration = await ctx.rpc.register(CostRpc,{summary:async input=>{
    if (typeof input.from !== "number" || typeof input.to !== "number" || input.from >= input.to) throw Error("invalid unchanged input");
    return reply;
  }});
  return () => registration.dispose();
}});
'''


class Terminal:
    def __init__(self, project, width=120, height=40):
        self.width, self.height = width, height
        self.screen = pyte.Screen(width, height)
        self.stream = pyte.Stream(self.screen)
        self.decoder = codecs.getincrementaldecoder('utf-8')('replace')
        self.raw = bytearray()
        self.pending = b''
        self.master, slave = pty.openpty()
        termios.tcsetwinsize(slave, (height, width))
        self.process = subprocess.Popen(
            ['opencode', '--standalone'], cwd=project, stdin=slave,
            stdout=slave, stderr=slave, start_new_session=True)
        os.close(slave)

    def send(self, data):
        os.write(self.master, data)

    def pump(self, seconds=0.2):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if not select.select([self.master], [], [], min(0.1, max(0, deadline-time.monotonic())))[0]:
                continue
            try:
                chunk = os.read(self.master, 65536)
            except OSError:
                break
            if not chunk:
                break
            self.raw.extend(chunk)
            if len(self.raw) > 1048576:
                del self.raw[:-1048576]
            # Match across read boundaries; answer only queries, never prompt text.
            data = self.pending + chunk
            pattern = rb'\x1b\[(?:\?|>)?[0-9;?]*[cnptuy]|\x1b\](?:10|11);\?\x1b\\'
            for match in re.finditer(pattern, data):
                query = match.group()
                response = {
                    b'\x1b[c': b'\x1b[?1;2c', b'\x1b[0c': b'\x1b[?1;2c',
                    b'\x1b[>c': b'\x1b[>0;1;0c', b'\x1b[>0c': b'\x1b[>0;1;0c',
                    b'\x1b[6n': b'\x1b[1;1R', b'\x1b[5n': b'\x1b[0n',
                    b'\x1b[?u': b'\x1b[?0u',
                    b'\x1b]10;?\x1b\\': b'\x1b]10;rgb:dddd/dddd/dddd\x1b\\',
                    b'\x1b]11;?\x1b\\': b'\x1b]11;rgb:1111/1111/1111\x1b\\',
                }.get(query)
                if query == b'\x1b[18t':
                    response = f'\x1b[8;{self.height};{self.width}t'.encode()
                if query == b'\x1b[14t':
                    response = f'\x1b[4;{self.height*16};{self.width*8}t'.encode()
                if response:
                    self.send(response)
            # Keep only an unfinished escape, avoiding duplicate query responses.
            last = data.rfind(b'\x1b')
            tail = data[last:] if last >= 0 else b''
            self.pending = tail if tail and not re.search(rb'[A-Za-z~\\]$', tail) and len(tail) < 128 else b''
            self.stream.feed(self.decoder.decode(chunk))

    def text(self):
        return '\n'.join(self.screen.display)

    def wait(self, text, timeout=20):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.pump()
            if text in self.text():
                return
            if self.process.poll() is not None:
                raise AssertionError(f'host exited {self.process.returncode} waiting for {text!r}')
        raise AssertionError(f'timed out waiting for {text!r}')

    def frame(self, name):
        self.pump(0.5)
        (EVIDENCE / f'{name}.txt').write_text(self.text())
        (EVIDENCE / f'{name}.raw').write_bytes(self.raw)
        for source in ['observer.json','observer-error.txt','observer-generations.txt']:
            path = Path('/work') / source
            if path.exists():
                (EVIDENCE / f'{name}-{source}').write_bytes(path.read_bytes()[-262144:])

    def click(self, text):
        self.wait(text)
        for y, row in enumerate(self.screen.display):
            x = row.find(text)
            if x >= 0:
                self.send(f'\x1b[<0;{x+1};{y+1}M\x1b[<0;{x+1};{y+1}m'.encode())
                self.pump(0.6)
                return
        raise AssertionError(f'click target absent: {text}')

    def resize(self, width, height=40):
        self.width, self.height = width, height
        termios.tcsetwinsize(self.master, (height, width))
        self.screen.resize(lines=height, columns=width)
        os.killpg(self.process.pid, signal.SIGWINCH)
        self.pump(1)

    def sidebar(self):
        self.send(b'\x1b[17~')
        self.pump(2)
        if 'This month' not in self.text():
            self.send(b'\x18b')  # public session.sidebar.toggle
        self.wait('This month',30)

    def close(self):
        try:
            os.killpg(self.process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(self.process.pid, signal.SIGKILL)
            self.process.wait(timeout=5)
        os.close(self.master)


def check(name, condition):
    RESULTS.append({'assertion': name, 'status': 'PASS' if condition else 'FAIL'})
    if not condition:
        raise AssertionError(name)


def observer_reply(terminal, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        terminal.pump(0.2)
        try:
            return json.loads(Path('/work/observer.json').read_text())['reply']
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    raise AssertionError('public RPC observer did not return a decoded reply')


def compatibility():
    baseline = {'revision':7,'totalMicros':250000,'complete':True,
                'agents':[{'agent':'fixture-agent','micros':250000}],
                'models':[{'model':'fixture-model','micros':250000}],
                'providers':[{'provider':'fixture-provider','micros':250000}]}
    for mode, total, complete in [('legacy',None,False),('null',None,False),('zero',0,True),('partial',700,False)]:
        root = Path('/work/compat-' + mode)
        root.mkdir()
        for var, name in [('HOME','home'),('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_STATE_HOME','state'),('XDG_CACHE_HOME','cache')]:
            os.environ[var] = str(root / name)
            (root / name).mkdir()
        fixture = root / 'fixture'
        fixture.mkdir()
        (fixture / 'package.json').write_text(json.dumps({'name':'cmon-compatibility-fixture','type':'module','exports':{'.':'./index.js','./tui':'./tui.js'}}))
        (fixture / 'index.js').write_text(COMPAT_SERVER)
        (fixture / 'tui.js').write_text('export {default} from "/opt/candidate/dist/tui.js";')
        expected = json.loads(json.dumps(baseline))
        if mode != 'legacy':
            expected['tokens'] = {'totalTokens':total,'complete':complete}
            for plural, key in [('agents','agent'),('models','model'),('providers','provider')]:
                expected['tokens'][plural] = [{key:'fixture-'+key,'totalTokens':total,'complete':complete}]
        (fixture / 'reply.json').write_text(json.dumps(expected))
        (root / 'opencode.json').write_text(json.dumps({'plugins':[fixture.as_uri()]}))
        Path('/work/observer.json').unlink(missing_ok=True)
        terminal = Terminal(root)
        try:
            terminal.wait('$0.25 this month',60)
            decoded = observer_reply(terminal)
            check(f'{mode}: real RPC decoded exact optional/null/zero/group fields', decoded == expected)
            (EVIDENCE / f'compat-{mode}-rpc.json').write_text(json.dumps(decoded,indent=2))
            terminal.sidebar()
            terminal.click('This month')
            terminal.wait('Tokens')
            terminal.click('Tokens')
            amount = 'Tokens unavailable' if total is None else ('~' if not complete else '') + str(total) + ' tokens'
            terminal.wait(amount)
            terminal.wait('[Tokens]')
            check(f'{mode}: rendered token amount via real click',amount in terminal.text())
            if not complete:
                check(f'{mode}: rendered partial warning','Partial:' in terminal.text())
            terminal.frame('compat-'+mode+'-tokens')
            terminal.click('$')
            terminal.wait('[$]')
            check(f'{mode}: switching restores identical dollars', '$0.25' in terminal.text())
            check(f'{mode}: switching preserves RPC values',observer_reply(terminal) == expected)
            terminal.frame('compat-'+mode+'-dollars')
        finally:
            try:
                terminal.frame('compat-'+mode+'-final')
            finally:
                terminal.close()
            RESULTS.append({'cleanup':mode+' host root terminated; container owns descendants','status':'PASS'})


def main():
    project = Path('/work/acceptance-project')
    project.mkdir()
    (project / 'opencode.json').write_text(json.dumps({'plugins': ['file:///opt/candidate/dist']}))
    observer = Path('/work/observer')
    observer.mkdir()
    (observer / 'package.json').write_text(json.dumps({'name':'cmon-acceptance-observer','type':'module','exports':{'./tui':'./tui.js'}}))
    (observer / 'tui.js').write_text(OBSERVER)
    os.environ['OPENCODE_CLI_CONFIG_CONTENT'] = json.dumps({'plugins':['file:///work/observer'], 'animations':False, 'highlights':False})
    terminal = Terminal(project)
    try:
        terminal.wait('$0.00 this month', 60)
        terminal.frame('host-home-zero')
        check('production empty RPC renders dollars in real home footer', '$0.00 this month' in terminal.text())
        terminal.sidebar()
        terminal.frame('host-sidebar-closed')
        terminal.click('This month')
        terminal.wait('Tokens')
        terminal.frame('host-sidebar-open')
        terminal.click('Tokens')
        terminal.wait('0 tokens')
        check('empty token mode reached by real mouse click', '[Tokens]' in terminal.text())
        for choice in ['Models','Providers','Agents']:
            terminal.click(choice)
            terminal.wait(f'[{choice}]')
            check(f'{choice} click does not collapse or reset unit', '[Tokens]' in terminal.text())
        terminal.frame('host-sidebar-tokens')
        terminal.send(b'\x1b[18~')  # observer F7: home route
        terminal.wait('0 tokens')
        terminal.frame('host-home-shared-tokens')
        check('home footer exposes complete shared token total', '▼ 0 tokens' in terminal.text())
        terminal.sidebar()
        terminal.wait('[Tokens]')
        terminal.click('This month')
        terminal.pump(0.5)
        check('collapse hides controls without losing token header', 'This month: 0 tokens' in terminal.text() and 'Unit' not in terminal.text())
        terminal.click('This month')
        terminal.wait('[Tokens]')
        check('reopen retains token mode', '[Tokens]' in terminal.text())
        terminal.frame('host-sidebar-remount')
        check('remount retains token selection', '[Tokens]' in terminal.text())
        check('production RPC preserves zero token totals',observer_reply(terminal)['tokens']['totalTokens'] == 0)
        if Path('/work/observer.json').exists():
            (EVIDENCE / 'host-observer.json').write_bytes(Path('/work/observer.json').read_bytes())
        # location.reload is documented as configuration reload, not guaranteed
        # plugin-generation replacement. The initial host run did not replace
        # this observer. Do not retry it or infer memory retention from no reload.
        RESULTS.append({'assertion':'plugin-generation reload and memory retention',
                        'status':'BLOCKED','detail':'Supported generation-reload trigger unresolved; configuration reload did not recreate observer.'})
        RESULTS.append({'assertion':'actual sidebar content geometry 45/40/22',
                        'status':'BLOCKED','detail':'No supported slot-sizing control established; terminal width is not panel width.'})
    finally:
        try:
            terminal.frame('host-final')
        finally:
            terminal.close()
        RESULTS.append({'cleanup': 'private host root terminated; container owns descendants', 'status': 'PASS'})
    terminal = Terminal(project)
    try:
        terminal.wait('$0.00',60)
        terminal.sidebar()
        terminal.wait('[$]')
        check('fresh host resets dollars while preserving open state','[$]' in terminal.text() and '[Tokens]' not in terminal.text())
        terminal.frame('host-restarted-dollars')
    finally:
        terminal.close()
        RESULTS.append({'cleanup':'restarted host root terminated; container owns descendants','status':'PASS'})
    compatibility()
    if any(item.get('status') in ('FAIL', 'BLOCKED') for item in RESULTS):
        raise AssertionError('remaining host gates are unresolved; see individual assertions')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        RESULTS.append({'assertion':'driver completion','status':'FAIL','detail':str(error)})
        raise
    finally:
        (EVIDENCE / 'acceptance-results.json').write_text(json.dumps(RESULTS, indent=2))
