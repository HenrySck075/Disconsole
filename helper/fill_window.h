#pragma once
//idk if this is how we create an header file, im noob at c++

#include <dpp/dpp.h>
#include <curses.h>
#include <windows.h>
#include <unordered_map>
#include <unordered.h>
#include <vector>
// fill win.guildList with names of every server the account in

std::vector<dpp::guild> fill_guilds(dpp::cluster*bot, WINDOW*win) {
    std::vector<dpp::guild> guilds = return_unordered_values(bot->current_user_get_guilds_sync());
    //addstr(std::to_string(d.guilds.size()).c_str());
    int i = 1;
    for (auto& guild : guilds) {
        waddnstr(win, guild.name.c_str(), 18);
        wmove(win, i, 1);
        i++;
    };
    wrefresh(win);
    return guilds;
};

std::vector<dpp::channel> fill_channels(dpp::cluster*bot, dpp::snowflake guildId, WINDOW* win) {
    std::vector<dpp::channel> channels = return_unordered_values(bot->channels_get_sync(guildId));
    int i = 1;
    for (auto& ch : channels) {
        waddnstr(win, ch.name.c_str(), 18);
        wmove(win, i, 1);
        i++;
    };
    wrefresh(win);
    return channels;
};

