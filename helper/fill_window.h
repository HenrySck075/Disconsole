#pragma once
//idk if this is how we create an header file, im noob at c++

#include <dpp/dpp.h>
#include <curses.h>
#include <windows.h>
#include <unordered_map>
#include <unordered.h>
#include <vector>
#include <other.h>
#include <variant>
#include <tuple>
#include <boost/format.hpp>

using boost::format;
using namespace std;
//2 first are params, 2 last are return value

std::tuple<vector<dpp::guild>,vector<string>> fill_guilds(dpp::cluster*bot) {

    vector<dpp::guild> guilds = return_unordered_values(bot->current_user_get_guilds_sync());
    vector<string> view;
    for (int i = 0; i < guilds.size(); i++) {
        dpp::guild g = guilds.at(i);
        format f = format("%1%. %2%") % to_string(i) % g.name;
        cout << g.name << "\n";
        view.push_back(f.str());
    };
    return {guilds,view};
    
};

//2 first are params, 2 last are return value
std::tuple<vector<dpp::channel>, vector<string>> fill_channels(dpp::cluster*bot, dpp::snowflake guildId) {
    vector<dpp::channel> channels = return_unordered_values(bot->channels_get_sync(guildId));
    vector<string> view;
    for (int i = 0; i < channels.size(); i++) {
        dpp::channel ch = channels.at(i);
        string declare;
        if (ch.is_category()) { declare = "v "; }
        else if (ch.is_text_channel()) { declare = "# "; }
        else if (ch.is_voice_channel()) { declare = "< "; }
        else if (ch.is_forum()) { declare = "P "; }
        else if (ch.is_stage_channel()) { declare = "^ "; };
        format e = format("%1%%2%") % declare % ch.name;
        view.push_back(e.str());
    };
    return { channels,view };
};

