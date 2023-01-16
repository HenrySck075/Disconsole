#include "MyBot.h"
#include <dpp/dpp.h>
#include <curses.h>
#include <windows.h>
#include <unordered_map>
#include <any>
#include <fill_window.h>
#include <codecvt>
#include <stdlib.h>
#include <wise_words.h>
#include <math.h>
#include <random>
#include <boost/format.hpp>
#include <boost/algorithm/string/join.hpp>
#include <other.h>

using namespace std;
using boost::format;
const string    BOT_TOKEN = "MTAxNDE0MTY4MDc5MTg2NzQxMw.Gq31q5.RUl0n1sw-9mmsS1t7-bk844IN6sOR7gPO0KYDc"; //jim resetted the token so this is now invalid
const string name = "Disconsole";
dpp::cluster bot(BOT_TOKEN);
bool ready = false;
struct FocusingData {
    vector<dpp::guild> guilds; //list of servers the account in    
    vector<dpp::channel> channels; //list of channels the (focusing) server have
    vector<dpp::message> messages; //list of message the (focusing) channel have (limited)
} d;
//like i said idfk what im doing
struct retu {
    vector<dpp::guild> guilds;
    vector<dpp::channel> channels;
    vector<dpp::message> messages;
    vector<string> view;
};
const short GUILD_BG[] = { 125,133,145 };
const short CHANNEL_BG[] = { 184,192,211 };
const short MAIN_BG[] = { 211,223,247 };
/* The content of the window
in order: win.guildList, win.channelList, win.messageList, win.memberList
*/
vector<vector<string>> view; 

/* The y position of the viewing content of the window
in order: win.guildList, win.channelList, win.messageList, win.memberList
*/
vector<int> pypos;

int state = 0; // normal, command, insert (send message)
// if you dont know what im doing, dont worry idk what im doing either
struct {
    WINDOW* message;
    WINDOW* cmd;
    WINDOW* guildList;
    WINDOW* channelList;
} win;
void set_title(string title) {
    wstring meat2(title.begin(), title.end());
    LPCWSTR h = meat2.c_str();
    SetConsoleTitle(h);
};
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
    };
    string last = rl.back();
    string newline = "\n";
    if (last.find(newline) != string::npos) {last.erase(last.length(), last.length()); }; // delete newline
    //scan
    if (rl[0] == "sel") {
        if (rl[1] == "server") {
            int idx = stoi(rl[2]);
            dpp::snowflake g = d.guilds[idx].id;
            wmove(win.channelList, 1, 1);
            vector<string> temp;
            tie(d.channels, temp) = fill_channels(&bot, g);

            pypos[1]=cscroll(win.channelList, &temp, 0, 0);
            wborder(win.channelList, 0, 0, 0, 0, ACS_TTEE, 0, ACS_BTEE, 0);
            wrefresh(win.channelList);
        }
    }
    else if (rl[0] == "exit") {
        bot.shutdown();
        endwin();
        bot.~cluster();
    }
    else if (rl[0] == "test") {
        cout << to_string(d.guilds.size()) << "\n";
    }
    else if (rl[0] == "debug") {
        format t = format("%1% | DEBUGVIEW mode") % name;
        noecho();
        set_title(t.str());
        def_prog_mode();
        endwin();
        print("--------You are viewing the debug log, press ESC to return to main window--------");
        while (1) {
            if (getch() == 27) {
                reset_prog_mode();
                refresh();
                wrefresh(win.guildList);
                wrefresh(win.cmd);
                wrefresh(win.channelList);
                break;
            };
            
        };
    }
    else {
        cout << "Ignoring " << boost::algorithm::join(rl, " ") << " as it's not a command" << "\n";
    };
};
void switch_mode() {
    if (state == 1) {
        format t = format("%1% | COMMAND mode") % name;
        set_title(t.str());
        wmove(win.cmd, 0, 0);
        echo();
        char* req = new char[999];
        while (1) {
            int meat = wgetch(win.cmd);
            if (meat == 10) { break; };
            if (meat == 27) {
                state = 0;
                set_title(name);
                noecho();
                return;
            }
        };
        wmove(win.cmd, 0, 0);
        winstr(win.cmd, req);
        wclrtobot(win.cmd);
        wrefresh(win.cmd);
        process_command(req);
        noecho();
        state = 0;
        set_title(name);
    };
    if (state == 0) {
        set_title(name);
        noecho();
        wrefresh(win.guildList);
    }
};

void key_event_log() {
    while (1) {
        if (ready) {
            int key = wgetch(win.guildList);
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
            case 67:
                if (state == 0) {
                    state = 1;
                };
                switch_mode();
            case 99:
                if (state == 0) {
                    state = 1;
                };
                switch_mode();
            }
        };
        Sleep(10);
    }
};
void close_message() {
    delwin(win.message);
    wrefresh(win.guildList);
    wrefresh(win.channelList);
};
/*Show a message on the first line of the window
if `int duration` is 0, then it'll show infinitely until `close_message` called*/
void print_message(string m, int duration = 0) {
    win.message = newwin(1, COLS, 0, 0);;
    waddstr(win.message, m.c_str());
    wrefresh(win.message);
    if (duration != 0) {
        Sleep(duration);
        close_message();
    };
};

void curser() {
    WINDOW* stdscr = initscr();
    setlocale(LC_ALL, "");
    int columns = COLS;
    int rows = LINES;
    keypad(stdscr, TRUE);

    noecho();

    win.cmd = newwin(1, columns-2, rows - 1, 2);
    win.guildList = newwin(rows - 1, 20, 0, 0);
    win.channelList = newwin(rows - 1, 20, 0, 19);
    box(win.guildList, 0, 0);
    wborder(win.channelList, 0, 0, 0, 0, ACS_TTEE, 0, ACS_BTEE, 0);
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
    //else {
        // TODO: make this message suppress-able
    //    print_message("Sorry, your console is unable to set colors", 6);
    //}
    string yk = "Did you know";
    string m = "Loading...";
    mvaddstr(LINES - 2, COLS / 2 - 5, m.c_str());
    mvaddstr(LINES / 2 + 1, COLS / 2 - 6, yk.c_str());
    // add random message
    std::random_device rd;
    std::mt19937 mt(rd());
    std::uniform_int_distribution<std::size_t> dist(0, 4);
    string rnd = random_words[dist(mt)];
    mvaddstr(LINES / 2 + 2, COLS / 2 - round(rnd.length()/2), rnd.c_str());
    refresh();
    wmove(win.guildList, 1, 1);
};

int main() {
    vector<string> emp;
    int empt=0;
    for (int i = 0; i < 4; i++) {
        view.push_back(emp);
        pypos.push_back(empt);
    };
    bot.on_log(dpp::utility::cout_logger());

    bot.on_slashcommand([&](const dpp::slashcommand_t& event) {
        if (event.command.get_command_name() == "ping") {
            event.reply("Pong!");
        }
    });


    bot.on_ready([&](const dpp::ready_t& event) {
        vector<string> temp;
        tie(d.guilds,temp)=fill_guilds(&bot);
        pypos[0] = cscroll(win.guildList, &temp, 0, 0);
        wborder(win.guildList, 0, 32, 0, 0, 0, 32, 0, 32);
        move(0, 0);
        clrtobot();
        ready = true;
        string cmdeco = "> ";
        mvaddstr(LINES - 1, 0, cmdeco.c_str());
        refresh();
        wrefresh(win.guildList);
        wrefresh(win.channelList);
        wrefresh(win.cmd);
        if (dpp::run_once<struct register_bot_commands>()) {
            bot.global_command_create(
                dpp::slashcommand("ping", "Ping", bot.me.id)
            );
        };
    });
    set_title(name);
    thread cons(curser);
    thread kel(key_event_log);
    bot.start(dpp::st_wait);
};

