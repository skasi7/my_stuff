/*
 * monty_hall: Simulation of The Monty Hall Problem
 * Authors = Rafael Treviño <skasi.7@gmail.com>
 * Date = 24/10/2013
 */

// Imports externals
#include <iostream>
#include <random>

// Imports internals


// Main entry point
int main(int argc, char** argv)
{
  std::random_device rd;
  std::mt19937 gen(rd());

  std::uniform_int_distribution<> car(1, 3);
  std::uniform_int_distribution<> choice(1, 3);
  std::uniform_int_distribution<> change(0, 1);

  unsigned int total = 100000;
  unsigned int stay_success = 0, change_success = 0;
  unsigned int stay_total = 0, change_total = 0;
  for (unsigned int n = 0; n < total; ++n) {
    int car_ = car(gen);
    int choice_ = choice(gen);
    int change_ = change(gen);
    if ((car_ == choice_) == (change_ == 0)) {
      if (change_ == 0) ++stay_success;
      else ++change_success;
    }
    if (change_ == 0) ++stay_total;
    else ++change_total;
  }

  double rate;
  rate = 100.0 * stay_success / stay_total;
  std::cout << "Stay success rate: " << rate << "%" << std::endl;
  rate = 100.0 * change_success / change_total;
  std::cout << "Change success rate: " << rate << "%" << std::endl;

  return 0;
}

