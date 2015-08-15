##
## vk-chat.py for weechat
## by lenormf
##
## URL to use to get a new auth_token
## http://api.vkontakte.ru/oauth/authorize?client_id=3382328&scope=messages,friends,offline&redirect_uri=blank.html&response_type=token
##
## Don't forget to "install" the weechat-plugin-vkontakte VK application, available here:
## http://vk.com/app3382328_185656651
##

import re
import time
import inspect

import vkontakte
import weechat

## Class definitions and their global instance
class Script:
    NAME = "vk-chat"
    AUTHOR = "Frank LENORMAND <lenormf@gmail.com>"
    VERSION = "0.1"
    LICENSE = "MIT"
    DESCRIPTION = "Chat with your friends on Vkontakte"

class Util:
    DEBUG = False

    @staticmethod
    def GetParentFunctionName():
        return inspect.stack()[2][3]

    @staticmethod
    def Log(s):
        log_str = u"{0}: {1}".format(Script.NAME, s)
        weechat.prnt("", log_str.encode("utf-8"))

    @staticmethod
    def Debug(s):
        if Util.DEBUG:
            log_str = u"[{0}][{1}]: {2}".format(time.ctime(), Util.GetParentFunctionName(), s)
            Util.Log(log_str)

    @staticmethod
    def GetConfigOption(option_name, type_=str):
        real_option_name = "python.{0}.{1}".format(Script.NAME, option_name)
        real_option_name_full = "plugins.var.{0}".format(real_option_name)

        if not weechat.config_is_set_plugin(option_name):
            Util.Debug("requesting an unexisting option: {0}".format(option_name))
            return None

        try:
            return type_(weechat.config_get_plugin(option_name))
        except:
            Util.Debug("error while casting option value to a {0}: {1}".format(type(type_).__name__, weechat.config_get_plugin(option_name)))
            return type_()

    @staticmethod
    def SetConfigOption(option_name, option_value):
        real_option_name = "python.{0}.{1}".format(Script.NAME, option_name)

        Util.Debug("setting configuration option: {0} = '{1}'".format(real_option_name, option_value))

        weechat.config_set_plugin(option_name, option_value)


class Plugin:
    DEFAULT_OPTIONS = [
        ("vk-token", ""),
        ("max-friends-suggestions", "10"),
    ]

    def __init__(self):
        self._timers = {}
        self._authed_vk = False
        self._vk_api = None
        self._friends = []

    def IsAuthedVkontakte(self):
        return self._authed_vk

    def AuthVkontakte(self, token):
        assert(isinstance(token, str))

        if self._authed_vk:
            Util.Debug("already authenticated")
            return True
        elif not token:
            Util.Debug("no token set for authentication")
            return False

        try:
            ## XXX: this plugin relies on version 5.21 of the VK API
            self._vk_api = vkontakte.API(token=token, v="5.21")
        except vkontakte.VKError as e:
            Util.Log("VKError: unable to log in")
            Util.Debug(u"{0}".format(e))
            return False
        except Exception as e:
            Util.Log("Unknown Exception: unable to log in")
            Util.Debug(u"{0}".format(e))
            return False
        else:
            Util.Log("successfully authentified to VK")
            self._authed_vk = True

        return True

    def GetFriends(self):
        return self._friends

    def FetchFriends(self):
        if not self._authed_vk:
            Util.Debug("unable to get the friends list: not authenticated")
            return False

        try:
            self._friends = self._vk_api.friends.get(order="hints", count=0, offset=0, fields="first_name,last_name,nickname", name_case="nom")
            self._friends = self._friends["items"]
        except vkontakte.VKError as e:
            Util.Log("VKError: unable to get a list of friends")
            Util.Debug(u"{0}".format(e))
            return False
        except Exception as e:
            Util.Log("Unknown Exception: unable to get a list of friends")
            Util.Debug(u"{0}".format(e))
            return False

        Util.Debug(u"pulled {0} friends: {1}".format(len(self._friends), self._friends))

        return True

    def FetchDialogs(self):
        dialogs = []

        if not self._authed_vk:
            Util.Debug("unable to get the dialogs: not authenticated")
            return False

        try:
            dialogs = self._vk_api.messages.getDialogs(offset=0, count=200, preview_length=0, unread=1)
            dialogs = dialogs["items"]
        except vkontakte.VKError as e:
            Util.Log("VKError: unable to get dialogs")
            Util.Debug(u"{0}".format(e))
            return False
        except Exception as e:
            Util.Log("Unknown Exception: unable to get dialogs")
            Util.Debug(u"{0}".format(e))
            return False

        Util.Debug(u"pulled {0} dialogs: {1}".format(len(dialogs), dialogs))

        return dialogs

    def MarkMessagesAsRead(self, ids):
        assert(isinstance(ids, list))

        try:
            self._vk_api.messages.markAsRead(message_ids=",".join(ids))
        except vkontakte.VKError as e:
            Util.Log("VKError: unable to mark messages as read")
            Util.Debug(u"{0}".format(e))
            return False
        except Exception as e:
            Util.Log("Unknown Exception: unable to mark messages as read")
            Util.Debug(u"{0}".format(e))
            return False

        Util.Debug("marked messages as read: {0}".format(ids))

        return True

    def SendMessageUid(self, uid, message):
        assert(isinstance(uid, unicode) or isinstance(uid, str))
        assert(isinstance(message, unicode) or isinstance(message, str))

        try:
            self._vk_api.messages.send(user_ids=uid.encode("utf-8"), message=message.encode("utf-8"))
        except vkontakte.VKError as e:
            Util.Log("VKError: unable to send messages")
            Util.Debug(u"{0}".format(e))
            return False
        except Exception as e:
            Util.Log("Unknown Exception: unable to send messages")
            Util.Debug(u"{0}".format(e))
            return False

        Util.Debug(u"sent message: {0}".format(message))

        return True

    def GetUnreadMessages(self):
        try:
            ## XXX: the filters variable doesn't seem to be returning unread messages only
            messages = self._vk_api.messages.get(count=5, time_offset=0, filters=1, preview_length=0, out=0)
            messages = [ message for message in messages["items"] if not message["read_state"] ]
        except vkontakte.VKError as e:
            Util.Log("VKError: unable to get unread messages")
            Util.Debug(u"{0}".format(e))
            return False
        except Exception as e:
            Util.Log("Unknown Exception: unable to get unread messages")
            Util.Debug(u"{0}".format(e))
            return False

        Util.Debug("unread messages received: {0}".format(messages))

        return messages

    def SetDefaultOptions(self):
        for k, v in self.DEFAULT_OPTIONS:
            option_value = Util.GetConfigOption(k)
            if not option_value:
                Util.SetConfigOption(k, v)
            else:
                Util.Debug("option {0} is already set to '{1}'".format(k, option_value))

    def SetCommands(self):
        weechat.hook_command("vkchat", "Chat with a friend on VK", "FIXME: document this command", "FIXME: document args", "FIXME: completion", "CallbackVkChat", "")

    def RegisterTimer(self, name, interval_ms, align_s, max_calls, callback_name, arg):
        assert(isinstance(name, unicode) or isinstance(name, str))
        assert(isinstance(interval_ms, int))
        assert(isinstance(align_s, int))
        assert(isinstance(max_calls, int))
        assert(isinstance(callback_name, str))

        Util.Debug("timer '{0}' registered".format(name))

        self._timers[name] = weechat.hook_timer(interval_ms, align_s, max_calls, callback_name, arg)

    def UnregisterTimer(self, name):
        assert(isinstance(name, unicode) or isinstance(name, str))

        if name in self._timers:
            Util.Debug("removing timer '{0}'".format(name))

            weechat.unhook(self._timers[name])
            del self._timers[name]
        else:
            Util.Debug("timer '{0}' was never registered, skipping")

plugin = Plugin()

class BufferManager(object):
    FMT_BUFFER_NAME = u"{first_name} {last_name} ({nickname})"

    def GetBuffer(self, buffer_id):
        assert(isinstance(buffer_id, unicode) or isinstance(buffer_id, str))

        return weechat.buffer_search("python", buffer_id.encode("utf-8"))

    def CreateBuffer(self, buffer_id, buffer_title, callback_name_oninput, callback_name_onclose, localvars):
        assert(isinstance(buffer_id, unicode) or isinstance(buffer_id, str))
        assert(isinstance(buffer_title, unicode) or isinstance(buffer_title, str))
        assert(isinstance(callback_name_oninput, str))
        assert(isinstance(callback_name_onclose, str))
        assert(isinstance(localvars, dict))

        buffer_ = self.GetBuffer(buffer_id)
        if buffer_:
            return buffer_

        buffer_ = weechat.buffer_new(buffer_id.encode("utf-8"), callback_name_oninput, "", callback_name_onclose, "")

        weechat.buffer_set(buffer_, "title", buffer_title.encode("utf-8"))

        for k, v in localvars.iteritems():
            Util.Debug(u"setting local variable {0} = '{1}'".format(k, v))
            weechat.buffer_set(buffer_, "localvar_set_{0}".format(k), v.encode("utf-8"))

        return buffer_

    def CreateChatBuffer(self, uid, first_name, last_name, nickname):
        assert(isinstance(uid, unicode) or isinstance(uid, str))
        assert(isinstance(first_name, unicode) or isinstance(first_name, str))
        assert(isinstance(last_name, unicode) or isinstance(last_name, str))
        assert(isinstance(nickname, unicode) or isinstance(nickname, str))

        buffer_title = u"{0} {1}, on Vkontakte".format(first_name, last_name)
        buffer_id = self.FMT_BUFFER_NAME.format(first_name=first_name, last_name=last_name, nickname=nickname if nickname else uid)

        return buffer_manager.CreateBuffer(buffer_id, buffer_title, "CallbackBufferInput", "CallbackBufferClose", {
                                                "first_name": first_name,
                                                "last_name": last_name,
                                                "uid": uid,
                                            })

    def DisplayMessageBuffer(self, buffer_, date, nick, message, outward):
        assert(isinstance(date, int))
        assert(isinstance(nick, unicode) or isinstance(nick, str))
        assert(isinstance(message, unicode) or isinstance(message, str))
        assert(isinstance(outward, bool))

        color = weechat.color("chat_nick_self" if outward else "chat_nick_other")
        message_body = u"{0}{1}\t{2}".format(color, nick, message)
        message_tags = u"notify_private,log1,nick_{0},prefix_nick_{1}".format(nick, color)

        weechat.prnt_date_tags(buffer_, date, message_tags.encode("utf-8"), message_body.encode("utf-8"))

    def DisplayMessagesSortedUid(self, friends, messages_by_uid):
        assert(isinstance(friends, list))
        assert(isinstance(messages_by_uid, dict))

        for uid, messages in messages_by_uid.iteritems():
            ## FIXME: this loop will not display messages received from non-friends
            for friend in friends:
                if friend["id"] != uid:
                    continue

                buffer_ = self.CreateChatBuffer(unicode(friend["id"]), friend["first_name"], friend["last_name"], friend["nickname"])
                for message in messages:
                    ## TODO: handle photos, emoticons and attachments

                    self.DisplayMessageBuffer(buffer_, message["date"], friend["first_name"], message["body"], False)

                plugin.MarkMessagesAsRead([ message["id"] for message in messages ])

                break

buffer_manager = BufferManager()

## Private functions
def _complete_friends_suggestions(friends, first_name, last_name):
    Util.Debug("completing '{0}' '{1}'".format(first_name, last_name))

    suggestions = []
    for friend in friends:
        f_first_name, f_last_name = friend["first_name"], friend["last_name"]
        match_fname = re.match(first_name, f_first_name, re.I) != None
        match_lname = re.match(last_name, f_last_name, re.I) != None

        if match_fname and match_lname:
            suggestions.append(friend)

    return suggestions

def _print_friends_suggestions(suggestions):
    max_friends_suggestions = Util.GetConfigOption("max-friends-suggestions", int)

    Util.Log("suggestions of friends to chat with (top {0}):".format(max_friends_suggestions))

    n = 0
    for friend in suggestions:
        first_name, last_name = friend["first_name"], friend["last_name"]

        if n >= max_friends_suggestions:
            break

        Util.Log(u"* {0} {1}".format(first_name, last_name))

        n += 1

def _sort_messages(messages):
    messages_by_uid = {}

    ## Separate the dialogs per user id
    for message in messages:
        if not message["user_id"] in messages_by_uid:
            messages_by_uid[message["user_id"]] = []

        messages_by_uid[message["user_id"]].append(message)

    ## Sort the messages for every user by date
    for uid, messages in messages_by_uid.iteritems():
        messages_by_uid[uid] = sorted(messages, key=lambda x: x["date"])

    return messages_by_uid

def _print_unread_dialogs(friends):
    dialogs = plugin.FetchDialogs()
    if not dialogs:
        return False

    dialogs_by_uid = _sort_messages([ dialog["message"] for dialog in dialogs ])

    if not friends:
        ## FIXME: if no friends were added, it's possible to resolve the contact name by uid with an API call
        Util.Debug("no friends in the list")
        return

    buffer_manager.DisplayMessagesSortedUid(friends, dialogs_by_uid)

    return True

## Callbacks
def CallbackBufferInput(_, buffer_, message):
    Util.Log(u"input: {0} ({1})".format(message.decode("utf-8"), type(message).__name__))

    ## TODO: replace smileys with the appropriate emoticons, if enabled in the config

    uid = weechat.buffer_get_string(buffer_, "localvar_uid")
    if uid:
        message = message.decode("utf-8")
        if plugin.SendMessageUid(unicode(uid), message):
            buffer_manager.DisplayMessageBuffer(buffer_, int(time.time()), u"me", message, True)

    return weechat.WEECHAT_RC_OK

def CallbackBufferClose(_, buffer_):
    ## XXX: is there anything to do here ?
    return weechat.WEECHAT_RC_OK

def CallbackVkChat(_, __, args):
    args = re.split("\s+", args)

    if not plugin.IsAuthedVkontakte():
        Util.Log("not authenticated yet")
        return weechat.WEECHAT_RC_OK

    friends = plugin.GetFriends()
    ## FIXME: can't talk to someone not already added as friend
    if not friends:
        Util.Log("add more friends to your VK profile to have someone to chat with")
        return weechat.WEECHAT_RC_OK
    ## TODO: add all the contacts that we have already talked to to the friends list

    Util.Debug(u"{0}".format(args))

    ## TODO: add a "help" command ?

    first_name = args[0] if len(args) > 0 else ".+"
    last_name = args[1] if len(args) > 1 else ".+"

    friends_match = _complete_friends_suggestions(friends, first_name, last_name)

    Util.Debug("found {0} suggestions for the given name combination: {1}".format(len(friends_match), friends_match))

    if len(friends_match) != 1:
        if not friends_match:
            _print_friends_suggestions(friends)
        else:
            _print_friends_suggestions(friends_match)

        return weechat.WEECHAT_RC_OK

    friend = friends_match[0]
    buffer_ = buffer_manager.CreateChatBuffer(unicode(friend["id"]), friend["first_name"], friend["last_name"], friend["nickname"])
    if buffer_:
        pass
        ## TODO: display newly open buffer
        ##weechat.buffer_switch(buffer_)

    return weechat.WEECHAT_RC_OK

def CallbackVkAuth(_, __):
    if plugin.IsAuthedVkontakte():
        ## XXX: return WEECHAT_RC_OK_EAT ?
        return weechat.WEECHAT_RC_OK

    config_token = Util.GetConfigOption("vk-token")
    if not config_token:
        Util.Log("no token has been set to authenticate with")
        ## TODO: add a hook that will auth when the vk-token option has changed
        return weechat.WEECHAT_RC_OK

    Util.Debug("config_token: '{0}'".format(config_token))

    if plugin.AuthVkontakte(config_token):
        ## Printing the unread messages relies on the friends list
        if plugin.FetchFriends():
            _print_unread_dialogs(plugin.GetFriends())

    return weechat.WEECHAT_RC_OK

def CallbackVkFetchFriends(_, __):
    if not plugin.IsAuthedVkontakte():
        Util.Debug("unable to get the friends list: not authenticated")
        return weechat.WEECHAT_RC_OK

    plugin.FetchFriends()
    ## TODO: add all the contacts that we have already talked to to the friends list

    return weechat.WEECHAT_RC_OK

def CallbackVkFetchMessages(_, __):
    if not plugin.IsAuthedVkontakte():
        Util.Debug("unable to get unread messages: not authenticated")
        return weechat.WEECHAT_RC_OK

    ## FIXME: use polling
    messages = plugin.GetUnreadMessages()
    if messages:
        buffer_manager.DisplayMessagesSortedUid(plugin.GetFriends(), messages)

    return weechat.WEECHAT_RC_OK

def CallbackPluginUnloaded():
    Util.Log("vk-chat unloaded")

    plugin.UnregisterTimer("vk-auth")
    plugin.UnregisterTimer("vk-fetch-friends")
    plugin.UnregisterTimer("vk-fetch-messages")

    return weechat.WEECHAT_RC_OK

## Entry point
def main():
    if weechat.register(Script.NAME, Script.AUTHOR, Script.VERSION, Script.LICENSE, Script.DESCRIPTION, "CallbackPluginUnloaded", ""):
        Util.Debug("plugin successfully registered")

        plugin.SetDefaultOptions()
        plugin.SetCommands()

        plugin.RegisterTimer("vk-auth", 60 * 1000, 60, 0, "CallbackVkAuth", "")
        plugin.RegisterTimer("vk-fetch-friends", 10 * 60 * 1000, 30, 0, "CallbackVkFetchFriends", "")
        plugin.RegisterTimer("vk-fetch-messages", 30 * 1000, 1, 0, "CallbackVkFetchMessages", "")

        ## Do not wait for the timers to be triggered in 60s
        CallbackVkAuth(None, -1)
        CallbackVkFetchFriends(None, -1)

if __name__ == "__main__":
    main()
