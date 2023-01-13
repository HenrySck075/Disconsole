#pragma once
#include <vector>
#include <dpp/dpp.h>
//idk if this is how we create an header file, im noob at c++

//Get all values from an unordered_map type namespace as std::vector
//@return
std::vector<dpp::guild> return_unordered_values(dpp::guild_map map) {
    std::vector<dpp::guild> vals;
    vals.reserve(map.size());

    for (auto kv : map) {
        vals.push_back(kv.second);
    };
    return vals;
};

//Get all values from an unordered_map type namespace as std::vector
std::vector<dpp::channel> return_unordered_values(dpp::channel_map map) {
    std::vector<dpp::channel> vals;
    vals.reserve(map.size());

    for (auto kv : map) {
        vals.push_back(kv.second);
    };
    return vals;
};

//Get all values from an unordered_map type namespace as std::vector
std::vector<dpp::message> return_unordered_values(dpp::message_map map) {
    std::vector<dpp::message> vals;
    vals.reserve(map.size());

    for (auto kv : map) {
        vals.push_back(kv.second);
    };
    return vals;
};
