from collections import namedtuple
from signal import signal, SIGINT
import sys
import threading
import time
from tqdm import tqdm
from types import FrameType as frame
from typing import Callable, Optional
from contextlib import contextmanager


# Wrapper around tqdm command-line progress bar.
class ProgressBar:

    @staticmethod
    @contextmanager
    def define(total: Optional[int] = None, description: Optional[str] = None,
               catch_interrupt: bool = True,
               interrupt: Optional[Callable] = None,
               interrupt_continue: Optional[Callable] = None,
               interrupt_stop: Optional[Callable] = None,
               interrupt_exit: bool = None,
               interrupt_message: Optional[str] = None,
               printf: Optional[Callable] = None,
               tidy_output_hack: bool = True) -> None:

        progress_bar = ProgressBar(
            total=total,
            description=description,
            catch_interrupt=catch_interrupt,
            interrupt=interrupt,
            interrupt_continue=interrupt_continue,
            interrupt_stop=interrupt_stop,
            interrupt_exit=interrupt_exit,
            interrupt_message=interrupt_message,
            printf=printf,
            tidy_output_hack=tidy_output_hack)
        try:
            yield progress_bar
        finally:
            progress_bar.done()

    def __init__(self, total: Optional[int] = None, description: Optional[str] = None,
                 catch_interrupt: bool = True,
                 interrupt: Optional[Callable] = None,
                 interrupt_continue: Optional[Callable] = None,
                 interrupt_stop: Optional[Callable] = None,
                 interrupt_exit: bool = False,
                 interrupt_message: Optional[str] = None,
                 printf: Optional[Callable] = None,
                 tidy_output_hack: bool = True) -> None:
        self._bar = None
        self._disabled = False
        self._done = False
        self._printf = printf if callable(printf) else print
        self._tidy_output_hack = (tidy_output_hack is True)
        self._started = time.time()
        self._stop_requested = False
        # Interrupt handling. We doo not in do the actual (signal) interrupt setup
        # in self._initialiaze as that could be called from a (sub) thread; and in
        # Python we can only set a signal (SIGINT in our case) on the main thread.
        self._catch_interrupt = (catch_interrupt is True)
        self._interrupt = interrupt if callable(interrupt) else None
        self._interrupt_continue = interrupt_continue if callable(interrupt_continue) else None
        self._interrupt_stop = interrupt_stop if callable(interrupt_stop) else None
        if interrupt_exit in [True, False]:
            if not self._interrupt_stop:
                self._interrupt_stop = lambda _: interrupt_exit
            self._interrupt_exit = interrupt_exit
        else:
            self._interrupt_exit = None
        self._interrupt_message = interrupt_message if isinstance(interrupt_message, str) else None
        self._interrupt_handler = None
        if self._catch_interrupt:
            self._interrupt_handler = self._define_interrupt_handler()
        if self._tidy_output_hack is True:
            self._tidy_output_hack = self._define_tidy_output_hack()
        # self.set_total(total)
        # self.set_description(description)
        self._total = total if isinstance(total, int) and total >= 0 else 0
        self._description = self._format_description(description)
        self._initialize()

    def _initialize(self) -> bool:
        # Do not actually create the tqdm object unless/until we have a positive total.
        if (self._bar is None) and (self._total > 0):
            bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt} | {rate_fmt} | {elapsed}{postfix} | ETA: {remaining} "
            self._bar = tqdm(total=self._total, desc=self._description,
                             dynamic_ncols=True, bar_format=bar_format, unit="", file=sys.stdout)
            if self._disabled:
                self._bar.disable = True
            return True
        return False

    def set_total(self, value: int) -> None:
        if isinstance(value, int) and value > 0:
            self._total = value
            if self._bar is not None:
                self._bar.total = value

    def set_progress(self, value: int) -> None:
        if isinstance(value, int) and value >= 0:
            if (self._bar is not None) or self._initialize():
                # Note that bar.update(0) is needed after bar.n assignment to make ETA correct.
                self._bar.n = value
                self._bar.update(0)

    def increment_progress(self, value: int) -> None:
        if isinstance(value, int) and value > 0:
            if (self._bar is not None) or self._initialize():
                self._bar.update(value)

    def set_description(self, value: str) -> None:
        self._description = self._format_description(value)
        if self._bar is not None:
            self._bar.set_description(self._description)

    def done(self) -> None:
        if self._done or self._bar is None:
            return
        self._ended = time.time()
        self._done = True
        self._bar.set_description(self._description)
        self._bar.update(0)
        # FYI: Do NOT do a bar.disable = True before a bar.close() or it messes up output
        # on multiple calls; found out the hard way; a couple hour will never get back :-/
        self._bar.close()
        if self._tidy_output_hack:
            self._tidy_output_hack.restore()
        if self._interrupt_handler:
            self._interrupt_handler.restore()

    def disable(self, value: bool = True) -> None:
        self._disabled = (value is True)
        if self._bar is not None:
            self._bar.disable = self._disabled

    def enable(self, value: bool = True) -> None:
        self.disable(not value)

    @property
    def total(self) -> int:
        return self._bar.total if self._bar else 0

    @property
    def progress(self) -> int:
        return self._bar.n if self._bar else 0

    @property
    def disabled(self) -> bool:
        return self._disabled

    @property
    def enabled(self) -> bool:
        return not self.disabled

    @property
    def stop_requested(self) -> bool:
        return self._stop_requested

    @property
    def started(self) -> None:
        return self._started

    @property
    def duration(self) -> None:
        return time.time() - self._started

    def _format_description(self, value: str) -> str:
        if not isinstance(value, str):
            value = ""
        if self._tidy_output_hack and not value.endswith("[progress]"):
            value += "[progress]"
        return value

    def _define_interrupt_handler(self) -> None:
        def handle_interrupt(signum: int, frame: frame) -> None:  # noqa
            nonlocal self
            def handle_secondary_interrupt(signum: int, frame: frame) -> None:  # noqa
                nonlocal self
                self._printf("\nEnter 'yes' to 'no' or CTRL-\\ to completely abort ...")
            self.disable()
            self._interrupt(self) if self._interrupt else None
            set_interrupt_handler(handle_secondary_interrupt)
            if self._confirmation(f"\nALERT! You have interrupted this {self._interrupt_message or 'process'}."
                                  f" Do you want to stop{' (exit)' if self._interrupt_exit else ''}?"):
                # Here there was an interrupt (CTRL-C) and the user confirmed (yes)
                # that they want to stop the process; if the interrupt_stop handler
                # is defined and returns True, then we exit the entire process here,
                # rather than simply returning, which is the default.
                if self._interrupt_stop:
                    interrupt_stop = self._interrupt_stop(self)
                    if (interrupt_stop is True) or ((interrupt_stop is None) and (self._interrupt_exit is True)):
                        self.done()
                        restore_interrupt_handler()
                        exit(1)
                    elif interrupt_stop is False or ((interrupt_stop is None) and (self._interrupt_exit is False)):
                        set_interrupt_handler(handle_interrupt)
                        interrupt_continue = self._interrupt_continue(self) if self._interrupt_continue else None
                        if not (interrupt_continue is False):
                            self.enable()
                        return
                self._stop_requested = True
                return
            set_interrupt_handler(handle_interrupt)
            self._interrupt_continue(self) if self._interrupt_continue else None
            self.enable()
        def restore_interrupt_handler() -> None:  # noqa
            nonlocal self, previous_interrupt_handler
            set_interrupt_handler(previous_interrupt_handler)
        def set_interrupt_handler(interrupt_handler: Callable) -> Optional[Callable]:  # noqa
            nonlocal self
            if callable(interrupt_handler) and (threading.current_thread() == threading.main_thread()):
                return signal(SIGINT, interrupt_handler)
            return None
        previous_interrupt_handler = set_interrupt_handler(handle_interrupt)
        return namedtuple("interrupt_handler", ["restore"])(restore_interrupt_handler)

    def _define_tidy_output_hack(self) -> None:
        def tidy_stdout_write(text: str) -> None:  # noqa
            nonlocal self, sys_stdout_write, spin_index, spin_chars
            # Very minor tqdm output tidy-up which was bugging me; tqdm forces a
            # colon (:) before the percentage, e.g. ":  25%|"; and while we're at
            # it do a little ASCII progress animation; this requires a "[progress]"
            # value in their display string where the progress bar should actually
            # go which we do in _format_description.
            if (self._disabled or self._done) and "[progress]:" in text:
                # And another hack to really disable output on interrupt;
                # on interrupt we set tqdm.disable to True, but output still
                # dribbles out, so if here the output looks like it is from
                # tqdm and we are disabled then do not output anything.
                return
            if "[progress]:" in text:
                spin_char = spin_chars[spin_index % len(spin_chars)] if not self._done else "| ✓"
                spin_index += 1
                text = text.replace("[progress]:", f" {spin_char} ")
            sys_stdout_write(text)
            sys.stdout.flush()
        def restore_stdout_write() -> None:  # noqa
            nonlocal sys_stdout_write
            if sys_stdout_write is not None:
                sys.stdout.write = sys_stdout_write
        sys_stdout_write = None
        spin_index = 0
        spin_chars = ["|", "/", "—", "\\"]
        if sys.stdout.write != tidy_stdout_write:
            sys_stdout_write = sys.stdout.write
            sys.stdout.write = tidy_stdout_write
        return namedtuple("tidy_output_hack", ["restore"])(restore_stdout_write)

    def _confirmation(self, message: Optional[str] = None) -> bool:
        # Effectively the same as dcicutils.command_utils.yes_or_no but with stdout flush.
        while True:
            if message:
                if not message.endswith(" "):
                    message += " "
                self._printf(message, end="")
                sys.stdout.flush()
            response = input()
            if not isinstance(response, str):
                return False
            if (response := response.strip().lower()) in ["yes", "y"]:
                return True
            if response in ["no", "n"]:
                return False
            self._printf("Please answer 'yes' or 'no'.")
            sys.stdout.flush()
