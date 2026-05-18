#pragma once
#include "ace_type.hpp"
#include "maps.hpp"
#include "proc_rw.hpp"
#include "scan_utils.hpp"
#include <functional>
#include <string>
#include <vector>

enum class E_string_encoding {
  ASCII,
  UTF8,
  UTF16LE,
};

enum class E_pattern_type {
  STRING,
  AOB,
};

struct pattern_match {
  ADDR address;
  std::vector<byte> matched_bytes;
  pattern_match(ADDR addr, const std::vector<byte> &bytes)
      : address(addr), matched_bytes(bytes) {}
};

class string_scanner {

private:
  const int pid;
  const size_t max_chunk_read_size = 1024 * 1024;
  proc_rw<byte> *process_rw = NULL;
  Scan_Utils::E_region_level region_level =
      Scan_Utils::E_region_level::all_read_write;
  std::vector<pattern_match> current_matches;
  bool first_scan_done = false;
  const std::function<void(size_t current, size_t max)> on_scan_progress;
  const std::function<void()> on_scan_done;

  void scan_chunk(byte *addr_start, byte *addr_end,
                  const std::vector<byte> &pattern,
                  const std::vector<bool> &mask);

public:
  string_scanner(
      int pid,
      std::function<void(size_t current, size_t max)> on_scan_progress,
      std::function<void()> on_scan_done = nullptr);
  ~string_scanner();

  void set_region_level(Scan_Utils::E_region_level level);
  Scan_Utils::E_region_level get_region_level() const;

  bool get_first_scan_done() const;
  void reset_scan();
  size_t get_match_count() const;
  const std::vector<pattern_match> &get_matches() const;

  void first_scan_string(const std::string &search_str,
                         E_string_encoding encoding, bool case_sensitive);

  void first_scan_aob(const std::string &aob_pattern);

  void next_scan_string(const std::string &search_str,
                        E_string_encoding encoding, bool case_sensitive);

  void next_scan_aob(const std::string &aob_pattern);

  void write_string_at(ADDR address, const std::string &value,
                       E_string_encoding encoding);
  void write_aob_at(ADDR address, const std::vector<byte> &bytes);

  static std::vector<byte> string_to_bytes(const std::string &str,
                                           E_string_encoding encoding);
  static std::vector<byte>
  parse_aob_pattern(const std::string &pattern, std::vector<bool> &mask);
};
