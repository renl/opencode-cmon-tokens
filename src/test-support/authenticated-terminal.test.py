"""Pure no-service checks for the Windows no-call driver."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("driver", Path(__file__).with_name("authenticated-terminal.py"))
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


class Safety(unittest.TestCase):
    def test_no_shared_service_api_path(self):
        source = Path(driver.__file__).read_text(encoding="utf-8")
        self.assertNotIn('["opencode", "api"', source)
        self.assertIn('ctx.client.plugin.list()', driver.OBSERVER)
        self.assertIn('ctx.client.location.get()', driver.OBSERVER)

    def test_explicit_session_agent_model_and_deny_all(self):
        source = Path(driver.__file__).read_text(encoding="utf-8")
        self.assertIn('agent:"general"', source)
        self.assertIn('providerID:"deepseek",id:"deepseek-flash"', source)
        self.assertIn('action:"*",resource:"*",effect:"deny"', source)

    def test_first_use_is_explicit_and_follows_empty_readiness(self):
        source = Path(driver.__file__).read_text(encoding="utf-8")
        self.assertIn('"--first-use",action="store_true"', source)
        self.assertIn('def worker(run, allow_first_use=False)', source)
        self.assertLess(source.index('write(run / "empty-render-verified.json"'), source.index('first_use(run,terminal'))
        self.assertIn('if allow_first_use:', source)
        self.assertIn('submitted=true;', driver.OBSERVER)
        self.assertEqual(driver.OBSERVER.count('ctx.client.session.prompt('), 1)
        self.assertIn('ctx.client.session.get({sessionID:session.id})', driver.OBSERVER)
        self.assertIn('current.agent!=="general"', driver.OBSERVER)
        self.assertIn('(run / "armed-session.json").unlink(missing_ok=True)', source)

    def test_opened_zero_footer_requires_unique_glyph_not_closed_caption(self):
        self.assertTrue(driver.opened_zero_dollars('  ▼ $0.00                              '))
        for text in ('▶ $0.00 this month', '▼ $0.00 this month', '▼ $0.00\n▼ $0.00',
                     '▼ $0.001', '▼ $0.00 Partial: unknown'):
            self.assertFalse(driver.opened_zero_dollars(text))

    def test_independent_compact_oracle(self):
        for total,expected in ((0,'0 tokens'),(1,'1 token'),(999,'999 tokens'),(1000,'1k tokens'),
                               (1234,'1.23k tokens'),(1235,'1.24k tokens'),(999995,'1M tokens'),
                               (1580000000,'1.58B tokens'),(1000000000000,'1000B tokens')):
            self.assertEqual(driver.compact_tokens(total,True),expected)
            self.assertEqual(driver.compact_tokens(total,False),'~'+expected)

    def test_containment_and_price_precede_admission(self):
        import inspect
        source=inspect.getsource(driver.first_use)
        self.assertLess(source.index('contained(['),source.index('write(run / "armed-session.json"'))
        self.assertLess(source.index('price=load('),source.index('write(run / "armed-session.json"'))
        self.assertIn('ledger(run)==snapshot',source)
        self.assertIn('requests["attempts"]*0.01',source)

    def test_user_prompt_is_not_assistant_confirmation(self):
        for text in ('Reply OK.', '┃ Reply OK.', 'Submitted Reply OK. successfully', 'OK request sent'):
            self.assertFalse(driver.assistant_confirmed(text))
        self.assertTrue(driver.assistant_confirmed('  OK  \n'))
        self.assertTrue(driver.assistant_confirmed('Reply OK.\n\n  OK.  \n'))

    def test_execution_is_bounded(self):
        with patch.object(driver.subprocess, "run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = "{}"
            driver.execute(["opencode", "api", "plugin.list"])
            self.assertEqual(run.call_args.kwargs["timeout"], 15)
            self.assertTrue(run.call_args.kwargs["capture_output"])

    def test_gate_private_launch_and_stable_observer_import(self):
        source = Path(driver.__file__).read_text(encoding="utf-8")
        self.assertIn('"docs/operations/windows-pty-gate.py"', source)
        self.assertIn('"--parent-pid", str(os.getpid()), "--", "opencode", "--standalone"', source)
        self.assertNotIn('%40', driver.OBSERVER)
        self.assertIn('observer-ready.json', driver.OBSERVER)
        self.assertIn('e?.stack', driver.OBSERVER)

    def test_observer_uses_host_public_sdk(self):
        self.assertIn('from "@opencode/plugin/tui"', driver.OBSERVER)
        self.assertNotIn('node_modules/', driver.OBSERVER)
        self.assertNotIn('from "effect/', driver.OBSERVER)
        source = Path(driver.__file__).with_name("host-terminal.py").read_text(encoding="utf-8")
        observer = source.split("OBSERVER = r'''", 1)[1].split("'''", 1)[0]
        self.assertIn('from "@opencode/plugin/tui"', observer)
        self.assertNotIn('node_modules/', observer)

    def test_zero_cannot_match_nonzero_or_dollar_rows(self):
        self.assertTrue(driver.exact_zero_tokens('This month\n 0 tokens'))
        for text in ('10 tokens', '1,000 tokens', '0 tokens\ngeneral $0.01',
                     '0 tokens\n$0', '0 tokens\nPartial: unknown'):
            with self.subTest(text=text):
                self.assertFalse(driver.exact_zero_tokens(text))

    def test_desired_open_state_clicks_only_when_needed(self):
        for initial in (True, False):
            for desired in (True, False):
                with self.subTest(initial=initial, desired=desired):
                    terminal = object.__new__(driver.Terminal)
                    terminal.run = Path("unused")
                    with patch.object(terminal, "open_state", side_effect=[initial, desired]), \
                         patch.object(terminal, "frame") as frame, \
                         patch.object(terminal, "click") as click, \
                         patch.object(terminal, "wait"), \
                         patch.object(terminal, "text", return_value="Unit" if desired else ""), \
                         patch.object(driver, "write") as write:
                        self.assertEqual(terminal.set_open(desired, "state"), initial)
                        self.assertEqual(click.call_count, int(initial != desired))
                        frame.assert_called_once_with("state-preaction")
                        self.assertEqual(write.call_args.args[1]["expectedToggle"], initial != desired)

    def test_wrong_state_after_single_click_fails_without_retry(self):
        terminal = object.__new__(driver.Terminal)
        terminal.run = Path("unused")
        with patch.object(terminal, "open_state", return_value=False), \
             patch.object(terminal, "frame"), patch.object(driver, "write"), \
             patch.object(terminal, "click") as click:
            with self.assertRaises(AssertionError):
                terminal.set_open(True, "state")
            click.assert_called_once_with("This month")

    def test_sidebar_uses_command_state_not_occluded_text(self):
        source = Path(driver.__file__).read_text(encoding="utf-8")
        self.assertNotIn('terminal.send("\\x18b")', source)
        self.assertIn('ctx.keymap.commands()', driver.OBSERVER)
        self.assertIn('c.id==="session.sidebar.toggle"', driver.OBSERVER)
        self.assertIn('["Hide sidebar","Show sidebar"]', driver.OBSERVER)
        self.assertIn('if(before!==desired)ctx.keymap.dispatch("session.sidebar.toggle")', driver.OBSERVER)
        self.assertIn('Owned sidebar test keys already bound', driver.OBSERVER)
        self.assertIn('ensureSidebar(originalSidebar)', driver.OBSERVER)
        self.assertLess(source.index('terminal.pump(5.5)'), source.index('terminal.set_open(True'))

    def test_public_command_ensure_is_idempotent_and_restores(self):
        # Execute the observer's actual command adapter against the documented SDK surface.
        import subprocess
        block = driver.OBSERVER.split('   let originalSidebar;', 1)[1].split('   for(const c', 1)[0]
        script = '''let originalSidebar; let visible=INITIAL, calls=0;
const fs={appendFileSync(){}}; const root="unused";
const ctx={keymap:{commands:()=>[{id:"session.sidebar.toggle",title:visible?"Hide sidebar":"Show sidebar"}],
dispatch:id=>{if(id!=="session.sidebar.toggle")throw Error("bad command");calls++;visible=!visible;}}};
''' + block + '''
ensureSidebar(true);ensureSidebar(true);
if(!visible||calls!==EXPECTED)throw Error("not idempotent");
ensureSidebar(originalSidebar);
if(visible!==INITIAL||calls!==EXPECTED*2)throw Error("not restored");
'''
        for initial in (True, False):
            result = subprocess.run(["bun", "-e", script.replace("INITIAL", str(initial).lower()).replace("EXPECTED", str(int(not initial)))],
                                    cwd=driver.ROOT, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
