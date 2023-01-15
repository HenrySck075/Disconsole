#pragma once
#include <string>
#include <vector>
#include <curses.h>
#include <stdlib.h>
//cout with endl bind to the end of the string
void print(std::string v) {
	std::cout << v << "\n";
};

//scroll workaround
int cscroll(WINDOW* win, std::vector<std::string>*view, int amount, int pos) {
	int y = getmaxy(win) - 2;//assume you used box
	int ypos = y + pos;
	std::vector<std::string> focus;
	wmove(win, 1, 1); wclrtobot(win);
	if (ypos < 0) { ypos = -1; }
	else {
		for (int i = 1; i < y + 1; i++) {
			wmove(win, i + pos, 1);
			if (i < view->size() + 1) {
				std::string item = view->at(i - 1 + pos);
				waddstr(win, item.substr(0, getmaxx(win) - 2).c_str());
			}
			else { break; }
		}
	};
	return ypos;
};