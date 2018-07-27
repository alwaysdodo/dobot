const axios = require("axios");
const {
    JSDOM
} = require("jsdom");

const fetch = require('node-fetch');
const botkit = require('botkit');
const keys = require('./keys');

const HOST_NAME = 'https://slack.com'

const controller = botkit.slackbot({
    debug: false,
    log: true
});

const botScope = [
    'direct_message',
    'direct_mention',
    'mention'
];

controller.hears('다음 두두는?', botScope, async (bot, message) => {
    var dday = await getDDay()
    bot.reply(message, `다음 두두는 .. ${dday}`);
});

controller.hears('낙서', ['direct_mention'], (bot, message) => {
    bot.reply(message, {
        attachments: [
            {
                title: "설명하기 힘들땐, 그려서 알려줘!",
                actions: [
                    {
                    type: "button",
                    text: "낙서하러 가자!",
                    url: `${keys.botDrawerDomain}?channel=${message.channel}`
                    }
                ]
            }
        ]
    });
});

async function postSlack() {
    const res = await fetch(`${HOST_NAME}/api/chat.postMessage`, {
        method: 'POST',
        headers: {
            'Content-type': 'application/json',
            'Authorization': `Bearer ${keys.botAPIToken}`
        },
        body: JSON.stringify({
            channel: 'general',
            text: '나도 .. '
        })
    })

    console.log(res)
}

async function getDDay() {
    const response = await axios.get("https://www.alwaysdodo.com/")

    const $dom = new JSDOM(response.data)
    const dday = $dom.window.document.getElementsByClassName("d-day")[0].innerHTML

    if (dday == "D-Day")
        return "아직 안정해졌어요오오오오오"
    else
        return `${dday.split('-')[1]} 일 남았어요오오오오오`
}

/** */

controller.spawn({
    token: keys.botAPIToken
}).startRTM();
