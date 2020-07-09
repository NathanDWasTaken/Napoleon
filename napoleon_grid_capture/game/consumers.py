from channels import Group


def ws_connect(message):
    Group('players').add(message.reply_channel)


def ws_disconnect(message):
    Group('players').discard(message.reply_channel)