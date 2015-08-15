
# Weechat VKontakte chat plugin

This plugin allows you to chat with your friends on the russian social network
[VKontakte](http://www.vk.com/) on [weechat](http://www.weechat.org/).

## Dependencies

* _vkontakte_ - https://github.com/kmike/vkontakte

## Installation

vk_chat.py uses an authentication token to connect to a _long polling_ server
(run by __VK__), which will send the plugin notifications each time someone
sends you a message.

Follow the following steps in order to get it to work:
* Install the application _weechat-plugin-vkontakte_ on __VK__ (http://vk.com/app3382328_185656651)
* Create an authorization token (http://api.vkontakte.ru/oauth/authorize?client_id=3382328&scope=messages,friends,offline&redirect_uri=blank.html&response_type=token)
* After following the above link, you will be asked to identify if you haven't logged in __VK__ (otherwise you can skip this step)  and to allow
the application to access your profile ; after going through those steps, you
will finally be redirected to a url which format is `https://oauth.vk.com/blank.html#access_token=<AUTH_TOKEN>&expires_in=0&user_id=<ID>`
* Copy the `AUTH_TOKEN` (it's a hash), and keep it secret: this information is as sensible as a
regular password
* Edit the configuration file for plugins, in the main directory (`$EDITOR ~/.weeechat/plugins.conf`), and
add the following line to the file (replace `AUTH_TOKEN` with the value you copied previously): `python.vk-chat.vk-token = <AUTH_TOKEN>`
* Finally, copy the file just like any other weechat script in the appropriate directory (`~/.weechat/python/`)

## Configuration

There are several variables that you can play around with to fit the plugin's behaviour to your needs:
* `max-friends-suggestions`: maximum amount of friends the `vkchat` command will return

You can modify those variables directly in the configuration file (`~/.weechat/plugins.conf` by default), or do from weechat with the following command template:  
`/set plugins.var.python.vk-chat.<VARIABLE> <VALUE>`  
where `VARIABLE` is the name of the configuration variable you want to change, and `VALUE` its value.

## Usage

Drop `vk-chat.py` in the `~/.weechat/python` directory and you're all set. You can additionally set the script to autoload, by creating a symlink to it:  
`ln -s ~/.weechat/python/vk_chat.py ~/.weechat/python/autoload/vk-chat.py`

## Commands

### `vkchat`

__Usage__: `/vkchat <first_name> [last_name]`

This command opens a new buffer which you can use to chat with someone. The `first_name` and `last_name` arguments can be the first/last name of the person you want to talk to,
but in reality they are regular expression patterns that will be matched against the names of your friends. The arguments are case insensitive.

If no argument is passed to the command, it will display a list of `max-friends-suggestions` names that you can chat with.
If only the `first_name` is passed to the command, it will assume the pattern `.+` for the `last_name` parameter.

__Examples__:
* `/vkchat Elena Putin`: talk to Elena Putin
* `/vkchat Elena`: talk to the only friend whose first name is Elena (if there are several contacts called Elena, the command will print their full names)
* `/vkchat`: print a list of `max-friends-suggestions` names that we can talk to
* `/vkchat el`: talk to the only friend whose first name starts with `el`, case sensitivity ignored
* `/vkchat el.+ .+`: same as above
