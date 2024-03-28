from collections import namedtuple
from signal import signal, SIGINT
from sys import stdout
from tqdm import tqdm
from types import FrameType as frame
from typing import Callable, Optional
from dcicutils.command_utils import yes_or_no


class ProgressBar:

    def __init__(self, total: Optional[int] = None, description: Optional[str] = None,
                 catch_interrupt: bool = True,
                 interrupt: Optional[Callable] = None,
                 interrupt_continue: Optional[Callable] = None,
                 interrupt_stop: Optional[Callable] = None,
                 interrupt_exit: bool = False,
                 interrupt_message: Optional[str] = None,
                 printf: Optional[Callable] = None,
                 tidy_output_hack: bool = True) -> None:
        self._total = total if isinstance(total, int) else 0
        self._description = description if isinstance(description, str) else ""
        self._bar = None
        self._disabled = False
        self._done = False
        self._printf = printf if callable(printf) else print
        self._tidy_output_hack = (tidy_output_hack is True)
        self._stdout_write = None
        self._index = 0
        # Interrupt handling.
        self._catch_interrupt = (catch_interrupt is True)
        self._interrupt = interrupt if callable(interrupt) else None
        self._interrupt_continue = interrupt_continue if callable(interrupt_continue) else None
        self._interrupt_stop = interrupt_stop if callable(interrupt_stop) else None
        if (interrupt_exit in [True, False]) and not self._interrupt_stop:
            self._interrupt_stop = lambda: interrupt_exit
            self._interrupt_exit = interrupt_exit
        else:
            self._interrupt_exit = False
        self._interrupt_message = interrupt_message if isinstance(interrupt_message, str) else None
        self._interrupt_handler = None
        # Not in self._initialiaze as that could be called from a (sub) thread;
        # and in Python can only set a signal (SIGINT in our case) on the main thread.
        if self._catch_interrupt:
            self._interrupt_handler = self._define_interrupt_handler()

    def _initialize(self):
        if self._tidy_output_hack:
            self._stdout_write = stdout.write
            chars = ["|", "/", "—", "\\"]
            def custom_stdout_write(text: str) -> None:  # noqa
                nonlocal self
                # Very minor tqdm output tidy-up which was bugging me;
                # tqdm forces a colon (:) before the percentage, e.g. ":  25%|".
                # and while we're at it do a little ASCII progress animation.
                # text = text.replace(" : ", " ▶ ")
                char = chars[self._index % len(chars)] if not self._done else "| ✓"; self._index += 1  # noqa
                # text = text.replace(" : ", f" {char} ")
                text = text.replace("[progress]:", f" {char} ")
                self._stdout_write(text)
                stdout.flush()
            stdout.write = custom_stdout_write
        bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt} | {rate_fmt} | {elapsed}{postfix} | ETA: {remaining} "
        self._bar = tqdm(total=self._total, desc=self._description,
                         dynamic_ncols=True, bar_format=bar_format, unit="", file=stdout)

    def set_total(self, value: int) -> None:
        self._total = value
        if self._bar is not None:
            self._bar.total = value

    def set_description(self, value: str) -> None:
        self._description = value
        if self._bar is not None:
            self._bar.set_description(value)

    def set_progress(self, value: str) -> None:
        self._initialize() if self._bar is None else None
        # Note that bar.update(0) is needed after bar.n assignment to make ETA correct.
        self._bar.n = value
        self._bar.update(0)

    def increment_progress(self, value: int) -> None:
        self._initialize() if self._bar is None else None
        self._bar.update(value)

    def done(self) -> None:
        self._initialize() if self._bar is None else None
        self._done = True
        self._bar.set_description(self._description)
        self._bar.update(0)
        # FYI: Do NOT do a bar.disable = True before a bar.close() or it messes up output
        # on multiple calls; found out the hard way; a couple hour will never get back :-/
        self._bar.close()
        if self._interrupt_handler:
            self._interrupt_handler.restore()
        if self._tidy_output_hack and self._stdout_write:
            stdout.write = self._stdout_write

    def disable(self, value: bool = True) -> None:
        self._disabled = (value is True)
        if self._bar is not None:
            self._bar.disable = self._disabled

    def enable(self, value: bool = True) -> None:
        self.disable(not value)

    def _define_interrupt_handler(self) -> None:
        def handle_interrupt(signum: int, frame: frame) -> None:  # noqa
            nonlocal self
            def handle_secondary_interrupt(signum: int, frame: frame) -> None:  # noqa
                nonlocal self
                self._printf("\nEnter 'yes' to 'no' or CTRL-\\ to completely abort ...")
            if self._am_main_thread():
                signal(SIGINT, handle_secondary_interrupt)
            self._interrupt() if self._interrupt else None
            if yes_or_no(f"\nALERT! You have interrupted this {self._interrupt_message or 'process'}."
                         f" Do you want to stop{' (exit)' if self._interrupt_exit else ''}?"):
                self.done()
                restore_interrupt_handler()
                # Here there was an interrupt (CTRL-C) and the user confirmed (yes)
                # that they want to stop the process; if the interrupt_stop handler
                # is defined and returns True, then we exit the entire process here,
                # rather than simply returning, which is the default.
                if (self._interrupt_stop() if self._interrupt_stop else None) is True:
                    exit(1)
                return
            if self._am_main_thread():
                signal(SIGINT, handle_interrupt)
            self._interrupt_continue() if self._interrupt_continue else None
        def restore_interrupt_handler() -> None:  # noqa
            nonlocal self, previous_interrupt_handler
            if (previous_interrupt_handler is not None) and self._am_main_thread():
                signal(SIGINT, previous_interrupt_handler)
        if self._am_main_thread():
            previous_interrupt_handler = signal(SIGINT, handle_interrupt)
        else:
            previous_interrupt_handler = None
        interrupt_handler_type = namedtuple("interrupt_handler", ["restore"])
        return interrupt_handler_type(restore_interrupt_handler)

    @staticmethod
    def _am_main_thread() -> bool:
        import threading
        return threading.current_thread() == threading.main_thread()
