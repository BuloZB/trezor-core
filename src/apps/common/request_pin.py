from trezor import ui
from trezor import wire
from trezor.utils import unimport

if __debug__:
    matrix = None


@unimport
async def request_pin_on_display(ctx: wire.Context, code: int=None) -> str:
    from trezor.messages.ButtonRequest import ButtonRequest
    from trezor.messages.ButtonRequestType import ProtectCall
    from trezor.messages.FailureType import PinCancelled
    from trezor.messages.wire_types import ButtonAck
    from trezor.ui.confirm import ConfirmDialog, CONFIRMED
    from trezor.ui.pin import PinMatrix
    from trezor import res

    if __debug__:
        global matrix

    _, label = _get_code_and_label(code)
    confirm = res.load(ui.ICON_CONFIRM)
    cancel = res.load(ui.ICON_CANCEL)
    clean = res.load(ui.ICON_CLEAR)

    await ctx.call(ButtonRequest(code=ProtectCall),
                   ButtonAck)

    def onchange():
        c = dialog.cancel
        if matrix.pin:
            c.content = clean
        else:
            c.content = cancel
        c.taint()
        c.render()

    ui.display.bar(0, 0, 240, 240, ui.C_SCREEN_BG)
    matrix = PinMatrix(label, with_zero=True)
    matrix.onchange = onchange
    dialog = ConfirmDialog(matrix, confirm, cancel)
    dialog.cancel.area = (0, 240 - 48, 80, 46)
    dialog.confirm.area = (240 - 80, 240 - 48, 80, 46)

    while True:
        res = await dialog
        pin = matrix.pin

        if res == CONFIRMED:
            matrix = None
            return pin
        elif res != CONFIRMED and pin:
            matrix.change('')
            continue
        else:
            matrix = None
            raise wire.FailureError(PinCancelled, 'PIN cancelled')


@unimport
async def request_pin_on_client(ctx: wire.Context, code: int=None) -> str:
    from trezor.messages.FailureType import PinCancelled
    from trezor.messages.PinMatrixRequest import PinMatrixRequest
    from trezor.messages.wire_types import PinMatrixAck, Cancel
    from trezor.ui.pin import PinMatrix

    if __debug__:
        global matrix

    code, label = _get_code_and_label(code)

    ui.display.bar(0, 0, 240, 240, ui.C_SCREEN_BG)
    matrix = PinMatrix(label)
    matrix.render()

    ack = await ctx.call(PinMatrixRequest(type=code),
                         PinMatrixAck, Cancel)
    digits = matrix.digits
    matrix = None

    if ack.MESSAGE_WIRE_TYPE == Cancel:
        raise wire.FailureError(PinCancelled, 'PIN cancelled')
    return _decode_pin(ack.pin, digits)


request_pin = request_pin_on_display


@unimport
async def request_pin_twice(ctx: wire.Context) -> str:
    from trezor.messages.FailureType import ActionCancelled
    from trezor.messages import PinMatrixRequestType

    pin_first = await request_pin(ctx, PinMatrixRequestType.NewFirst)
    pin_again = await request_pin(ctx, PinMatrixRequestType.NewSecond)
    if pin_first != pin_again:
        # changed message due to consistency with T1 msgs
        raise wire.FailureError(ActionCancelled, 'PIN change failed')

    return pin_first


async def protect_by_pin_repeatedly(ctx: wire.Context, at_least_once: bool=False):
    from . import storage

    locked = storage.is_locked() or at_least_once
    while locked:
        pin = await request_pin(ctx)
        locked = not storage.unlock(pin, _render_pin_failure)


async def protect_by_pin_or_fail(ctx: wire.Context, at_least_once: bool=False):
    from trezor.messages.FailureType import PinInvalid
    from . import storage

    locked = storage.is_locked() or at_least_once
    if locked:
        pin = await request_pin(ctx)
        if not storage.unlock(pin, _render_pin_failure):
            raise wire.FailureError(PinInvalid, 'PIN invalid')


protect_by_pin = protect_by_pin_or_fail


def _render_pin_failure(sleep_ms: int):
    ui.display.clear()
    ui.display.text_center(240, 240, 'Sleeping for %d seconds' % (sleep_ms / 1000),
                           ui.BOLD, ui.RED, ui.BLACK)


def _get_code_and_label(code: int):
    from trezor.messages import PinMatrixRequestType
    if code is None:
        code = PinMatrixRequestType.Current
    if code == PinMatrixRequestType.NewFirst:
        label = 'Enter new PIN'
    elif code == PinMatrixRequestType.NewSecond:
        label = 'Enter PIN again'
    else:  # PinMatrixRequestType.Current
        label = 'Enter PIN'
    return code, label


def _decode_pin(pin: str, secret: list) -> str:
    return ''.join([str(secret[int(d) - 1]) for d in pin])
