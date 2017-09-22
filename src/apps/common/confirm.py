from trezor import wire, ui, loop
from trezor.utils import unimport

# used to confirm/cancel the dialogs from outside of this module (i.e.
# through debug link)
if __debug__:
    signal = loop.signal()


@unimport
async def confirm(ctx, content, code=None, *args, **kwargs):
    from trezor.ui.confirm import ConfirmDialog, CONFIRMED
    from trezor.messages.ButtonRequest import ButtonRequest
    from trezor.messages.ButtonRequestType import Other
    from trezor.messages.wire_types import ButtonAck

    ui.display.clear()
    dialog = ConfirmDialog(content, *args, **kwargs)
    dialog.render()

    if code is None:
        code = Other
    await ctx.call(ButtonRequest(code=code), ButtonAck)

    if __debug__:
        waiter = loop.wait(signal, dialog)
    else:
        waiter = dialog
    return await waiter == CONFIRMED


@unimport
async def hold_to_confirm(ctx, content, code=None, *args, **kwargs):
    from trezor.ui.confirm import HoldToConfirmDialog, CONFIRMED
    from trezor.messages.ButtonRequest import ButtonRequest
    from trezor.messages.ButtonRequestType import Other
    from trezor.messages.wire_types import ButtonAck

    # ui.display.clear()
    ui.display.bar(0, 0, 240, 240, ui.C_SCREEN_BG)
    dialog = HoldToConfirmDialog(content, 'Hold to send', *args, **kwargs)

    if code is None:
        code = Other
    await ctx.call(ButtonRequest(code=code), ButtonAck)

    if __debug__:
        waiter = loop.wait(signal, dialog)
    else:
        waiter = dialog
    return await waiter == CONFIRMED


@unimport
async def require_confirm(*args, **kwargs):
    from trezor.messages.FailureType import ActionCancelled

    confirmed = await confirm(*args, **kwargs)

    if not confirmed:
        raise wire.FailureError(ActionCancelled, 'Cancelled')
