#include "MyBot.h"
#include <dpp/dpp.h>
#include <curses.h>
#include <windows.h>
#include <unordered_map>
#include <any>
#include <fill_window.h>
#include <codecvt>
#include <stdlib.h>
using namespace std;
const string    BOT_TOKEN = "you dont lmao";
dpp::cluster bot(BOT_TOKEN);
WINDOW* message;
struct FocusingData {
    vector<dpp::guild> guilds; //list of servers the account in
    vector<dpp::channel> channels; //list of channels the (focusing) server have
    vector<dpp::message> messages; //list of message the (focusing) channel have (limited)
} d;
const short GUILD_BG[] = { 125,133,145 };
const short CHANNEL_BG[] = { 184,192,211 };
const short MAIN_BG[] = { 211,223,247 };

int state = 0; // normal, command, insert (send message)
// if you dont know what im doing, dont worry idk what im doing either
struct {
    WINDOW* cmd;
    WINDOW* guildList;
    WINDOW* channelList;
} win;

void process_command(string req) {
    //split
    size_t pos = 0;
    string token, delimiter;
    delimiter = " ";
    vector<string> rl;
    while ((pos = req.find(delimiter)) != string::npos) {
        token = req.substr(0, pos);
        rl.push_back(token);
        req.erase(0, pos + delimiter.length());
    }

    //scan
    if (rl[0] == "sel") {
        if (rl[1] == "server") {
            int idx = stoi(rl[2]);
            dpp::snowflake g = d.guilds[idx].id;
            d.channels = fill_channels(&bot, g, win.channelList);
        }
    }
}
void switch_mode() {
    if (state == 1) {
        echo();
        char* req = new char[999];
        while (1) {
            int meat = wgetch(win.cmd);
            if (meat == 10) { break; };
            if (meat == 27) {
                state = 0;
                noecho();
                break;
            }
        };
        wmove(win.cmd, 0, 2);
        winstr(win.cmd, req);
        process_command(req);
        noecho();
    };
    if (state == 0) {
        noecho();
        wrefresh(win.guildList);
    }
};
void key_event_log() {
    while (1) {
        int key = wgetch(win.guildList);
        string meat = to_string(key) + " | " + to_string(state);
        wstring meat2(meat.begin(), meat.end());
        LPCWSTR h = meat2.c_str();
        SetConsoleTitle(h);
        switch (key) {
        case 27:
            // i dont see the part where this thing works as expected
            if (state == 2) {
                state = 0;
            }
            else if (state == 1) {
                state = 0;
            };
            switch_mode();
        case 73:
            if (state == 0) {
                state = 1;
            };
            switch_mode();
        case 105:
            if (state == 0) {
                state = 1;
            };
            switch_mode();
        }
    }
};
/*Show a message on the first line of the window
if `int duration` is 0, then it'll show infinitely until `close_message` called*/
void print_message(string m, int duration = 0) {
    message = newwin(1, COLS, 0, 0);;
    waddstr(message, m.c_str());
    wrefresh(message);
    if (duration != 0) {
        Sleep(duration);
    };
};
void close_message() {
    delwin(message);
    wrefresh(win.guildList);
    wrefresh(win.channelList);
}
void curser() {
    WINDOW* stdscr = initscr();
    int columns = COLS;
    int rows = LINES;
    keypad(stdscr, TRUE);
    noecho();

    win.cmd = newwin(1, columns, rows - 1, 0);
    win.guildList = newwin(rows - 1, 20, 0, 0);
    win.channelList = newwin(rows - 1, 19, 0, 20);
    box(win.guildList, 0, 0);
    wborder(win.channelList, 30, 0, 0, 0, 9520, 0, 9529, 0);
    //only init colors if it can, else no
    //temporary disabled so it won't looks ugly on teminals that `has_color` but can't color fsr
    if (0) {
        start_color();
        init_color(1, GUILD_BG[0], GUILD_BG[1], GUILD_BG[2]);
        init_color(2, CHANNEL_BG[0], CHANNEL_BG[1], CHANNEL_BG[2]);
        init_color(3, MAIN_BG[0], MAIN_BG[1], MAIN_BG[2]);
        init_pair(1, 1, 7);
        init_pair(2, 2, 7);
        init_pair(3, 3, 7);
        bkgd(3);
        wbkgd(win.guildList, 1);
        wbkgd(win.channelList, 2);
    }
    else {
        // TODO: make this message suppress-able
        print_message("Sorry, your console is unable to set colors", 6);
    }
    wmove(win.guildList, 1, 1);
    string cmdeco = "> ";
    waddstr(win.cmd, cmdeco.c_str());
    wrefresh(win.guildList);
    wrefresh(win.channelList);
    wrefresh(win.cmd);
};

int main() {
    bot.on_log(dpp::utility::cout_logger());

    bot.on_slashcommand([&](const dpp::slashcommand_t& event) {
        if (event.command.get_command_name() == "ping") {
            event.reply("Pong!");
        }
        });


    bot.on_ready([&](const dpp::ready_t& event) {
        d.guilds = fill_guilds(&bot, win.guildList);
    if (dpp::run_once<struct register_bot_commands>()) {
        bot.global_command_create(
            dpp::slashcommand("ping", "Ping", bot.me.id)
        );
    };
        });
    thread cons(curser);
    thread kel(key_event_log);
    bot.start(dpp::st_wait);
};

