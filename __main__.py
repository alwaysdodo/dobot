import os
import time
import json
from subprocess import Popen
from urllib.request import urlopen
from slackclient import SlackClient

slack_token = os.environ.get("SLACK_API_TOKEN")
sc = SlackClient(slack_token)

users = sc.api_call('users.list')
user_info = {user.get('id'): {'email': user.get('profile').get('email'), 'name': user.get('name')} for user in
             users.get('members')}


def post_message(channel_id, text):
    return sc.api_call(
        "chat.postMessage",
        channel=channel_id,
        text=text,
    )


def get_path(*path):
    script_dir = os.path.realpath(os.path.dirname(__file__))
    return os.path.join(script_dir, *path)


def target_date():
    data = urlopen('https://raw.githubusercontent.com/alwaysdodo/alwaysdodo.github.io/source/assets/json/meets.json')
    json_data = json.loads(data.read())
    date = max((d.get('date') for d in json_data['meets'] if d.get('date')))
    return date


TEMPLATE = '''
---
name: {name}
---

## 오늘 어떤 일을 하셨나요?

{conversation.activity[a1][text]}

## 두두에 바라는 점을 말씀해 주세요.

{conversation.activity[a2][text]}
 
'''


class Conversation:
    def __init__(self, user, channel):
        self.user = user
        self.user_dm = channel
        self.activity = {}
        self.first_dodo()

    def question(self, message):
        return post_message(self.user_dm, message)

    def first_dodo(self):
        resp = self.question('안녕하세요! 오늘 어떤 일을 하셨나요?')
        self.activity.update(q1=resp)

    def second_dodo(self):
        resp = self.question('두두에 바라는 점을 말씀해 주세요.')
        self.activity.update(q2=resp)

    def flush_conversation(self):
        """
        github commit, send slack channel
        :return:
        """
        self.question('감사해요! 수고하셨습니다 :tada:')
        username = user_info.get(self.user).get('name')
        user_email = user_info.get(self.user).get('email')
        target_repo = get_path(os.environ.get('DODO_WORKS'), target_date(), username + '.md')

        with open(target_repo, 'w') as f:
            f.write(TEMPLATE.format(name=username, conversation=self))

        Popen(
            '''nohup sh -c "git -C {repo} pull && git -C {repo} add {target} && git -C {repo} commit --author='{name} <{email}>' -m '{name} commit' {target} && git -C {repo} push" &'''.format(
                repo=os.environ.get('DODO_WORKS'), target=target_repo, name=username, email=user_email),
            shell=True)

        # '''nohup sh -c 'git -C $me/works commit --author="{email}" -m "test" 2018-07-20/{name}.md' &'''


def force_trigger():
    im_list = sc.api_call('im.list')
    im_info = [(im.get('id'), im.get('user')) for im in im_list.get('ims')]
    for dm, user in im_info:
        global_d[user] = Conversation(user, dm)


def stand_up(e):
    user = e.get('user')
    text = e.get('text')
    if not user or not text:
        return

    channel = e.get('channel', '')
    if channel.startswith('D'):
        text = e.get('text', '')

        if text.startswith('standup'):
            global_d[user] = Conversation(user, channel)

        elif user in global_d:
            conversation = global_d[user]

            if conversation.activity.get('q2'):
                conversation.activity.update(a2=e)
                conversation.flush_conversation()
                global_d.pop(user)
            elif conversation.activity.get('q1'):
                conversation.activity.update(a1=e)
                conversation.second_dodo()


global_d = {}

if __name__ == '__main__':

    if sc.rtm_connect(with_team_state=False):
        while True:
            # if flag and datetime.now() > datetime(hour=5, minute=7)

            for event in sc.rtm_read():
                print(event)
                stand_up(event)

            time.sleep(1)
    else:
        print('Connection Failed')
