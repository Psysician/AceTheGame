#include "ACE/string_scanner.hpp"
#include "ACE/maps.hpp"
#include "ACE/to_frontend.hpp"
#include <algorithm>
#include <cctype>
#include <cstring>
#include <sstream>

string_scanner::string_scanner(
    int pid,
    std::function<void(size_t current, size_t max)> on_scan_progress,
    std::function<void()> on_scan_done)
    : pid(pid), on_scan_progress(on_scan_progress), on_scan_done(on_scan_done) {
  this->process_rw = new proc_rw<byte>(pid);
}

string_scanner::~string_scanner() { delete this->process_rw; }

void string_scanner::set_region_level(Scan_Utils::E_region_level level) {
  this->region_level = level;
}

Scan_Utils::E_region_level string_scanner::get_region_level() const {
  return this->region_level;
}

bool string_scanner::get_first_scan_done() const {
  return this->first_scan_done;
}

void string_scanner::reset_scan() {
  this->current_matches.clear();
  this->first_scan_done = false;
}

size_t string_scanner::get_match_count() const {
  return this->current_matches.size();
}

const std::vector<pattern_match> &string_scanner::get_matches() const {
  return this->current_matches;
}

std::vector<byte> string_scanner::string_to_bytes(const std::string &str,
                                                  E_string_encoding encoding) {
  std::vector<byte> bytes;
  switch (encoding) {
  case E_string_encoding::ASCII:
  case E_string_encoding::UTF8:
    for (char c : str) {
      bytes.push_back(static_cast<byte>(c));
    }
    break;
  case E_string_encoding::UTF16LE:
    for (char c : str) {
      bytes.push_back(static_cast<byte>(c));
      bytes.push_back(0);
    }
    break;
  }
  return bytes;
}

std::vector<byte>
string_scanner::parse_aob_pattern(const std::string &pattern,
                                  std::vector<bool> &mask) {
  std::vector<byte> bytes;
  mask.clear();
  std::istringstream stream(pattern);
  std::string token;

  while (stream >> token) {
    if (token == "?" || token == "??" || token == "xx") {
      bytes.push_back(0);
      mask.push_back(false);
    } else {
      unsigned int val = 0;
      try {
        val = std::stoul(token, nullptr, 16);
      } catch (...) {
        val = 0;
      }
      bytes.push_back(static_cast<byte>(val & 0xFF));
      mask.push_back(true);
    }
  }
  return bytes;
}

void string_scanner::scan_chunk(byte *addr_start, byte *addr_end,
                                const std::vector<byte> &pattern,
                                const std::vector<bool> &mask) {
  if (pattern.empty())
    return;

  size_t pattern_len = pattern.size();
  size_t region_size = (size_t)(addr_end - addr_start);
  if (region_size < pattern_len)
    return;

  size_t buff_size = std::min(region_size, max_chunk_read_size + pattern_len);
  std::vector<byte> buffer(buff_size);

  size_t offset = 0;
  while (offset < region_size) {
    size_t read_size = std::min(buff_size, region_size - offset);
    ssize_t bytes_read = process_rw->read_mem_new(
        addr_start + offset, read_size, buffer.data());

    if (bytes_read <= 0 || (size_t)bytes_read < pattern_len)
      break;

    size_t search_end = (size_t)bytes_read - pattern_len;
    for (size_t i = 0; i <= search_end; i++) {
      bool found = true;
      for (size_t j = 0; j < pattern_len; j++) {
        if (mask[j] && buffer[i + j] != pattern[j]) {
          found = false;
          break;
        }
      }
      if (found) {
        ADDR match_addr = (ADDR)(addr_start + offset + i);
        std::vector<byte> matched(pattern_len);
        std::memcpy(matched.data(), &buffer[i], pattern_len);
        current_matches.emplace_back(match_addr, matched);
      }
    }

    if (read_size >= buff_size) {
      offset += buff_size - pattern_len + 1;
    } else {
      break;
    }
  }
}

void string_scanner::first_scan_string(const std::string &search_str,
                                       E_string_encoding encoding,
                                       bool case_sensitive) {
  this->current_matches.clear();

  std::string effective_str = search_str;
  if (!case_sensitive) {
    std::transform(effective_str.begin(), effective_str.end(),
                   effective_str.begin(), ::tolower);
  }

  std::vector<byte> pattern = string_to_bytes(effective_str, encoding);
  std::vector<bool> mask(pattern.size(), true);

  if (!case_sensitive && encoding != E_string_encoding::UTF16LE) {
    std::vector<byte> upper_pattern =
        string_to_bytes(search_str, encoding);
    for (size_t i = 0; i < upper_pattern.size(); i++) {
      char c = (char)upper_pattern[i];
      if (std::isalpha(c)) {
        mask[i] = false;
      }
    }
    mask.assign(pattern.size(), true);
  }

  std::vector<struct mem_region> regions =
      mem_region_get_regions_for_scan(this->pid, this->region_level);

  size_t total_regions = regions.size();
  for (size_t i = 0; i < total_regions; i++) {
    scan_chunk((byte *)regions[i].address_start,
               (byte *)regions[i].address_end, pattern, mask);
    if (on_scan_progress) {
      on_scan_progress(i + 1, total_regions);
    }
  }

  this->first_scan_done = true;
  if (on_scan_done) {
    on_scan_done();
  }
}

void string_scanner::first_scan_aob(const std::string &aob_pattern) {
  this->current_matches.clear();

  std::vector<bool> mask;
  std::vector<byte> pattern = parse_aob_pattern(aob_pattern, mask);

  if (pattern.empty()) {
    frontend::mark_task_fail("Empty AOB pattern\n");
    return;
  }

  std::vector<struct mem_region> regions =
      mem_region_get_regions_for_scan(this->pid, this->region_level);

  size_t total_regions = regions.size();
  for (size_t i = 0; i < total_regions; i++) {
    scan_chunk((byte *)regions[i].address_start,
               (byte *)regions[i].address_end, pattern, mask);
    if (on_scan_progress) {
      on_scan_progress(i + 1, total_regions);
    }
  }

  this->first_scan_done = true;
  if (on_scan_done) {
    on_scan_done();
  }
}

void string_scanner::next_scan_string(const std::string &search_str,
                                      E_string_encoding encoding,
                                      bool case_sensitive) {
  std::vector<byte> pattern = string_to_bytes(search_str, encoding);
  std::vector<bool> mask(pattern.size(), true);

  std::vector<pattern_match> new_matches;
  std::vector<byte> buffer(pattern.size());

  for (const auto &match : current_matches) {
    ssize_t bytes_read = process_rw->read_mem_new(
        (byte *)match.address, pattern.size(), buffer.data());

    if (bytes_read < (ssize_t)pattern.size())
      continue;

    bool found = true;
    for (size_t j = 0; j < pattern.size(); j++) {
      byte b = buffer[j];
      byte p = pattern[j];
      if (!case_sensitive) {
        b = (byte)std::tolower((unsigned char)b);
        p = (byte)std::tolower((unsigned char)p);
      }
      if (mask[j] && b != p) {
        found = false;
        break;
      }
    }
    if (found) {
      new_matches.emplace_back(match.address, buffer);
    }
  }

  current_matches = std::move(new_matches);
}

void string_scanner::next_scan_aob(const std::string &aob_pattern) {
  std::vector<bool> mask;
  std::vector<byte> pattern = parse_aob_pattern(aob_pattern, mask);

  std::vector<pattern_match> new_matches;
  std::vector<byte> buffer(pattern.size());

  for (const auto &match : current_matches) {
    ssize_t bytes_read = process_rw->read_mem_new(
        (byte *)match.address, pattern.size(), buffer.data());

    if (bytes_read < (ssize_t)pattern.size())
      continue;

    bool found = true;
    for (size_t j = 0; j < pattern.size(); j++) {
      if (mask[j] && buffer[j] != pattern[j]) {
        found = false;
        break;
      }
    }
    if (found) {
      new_matches.emplace_back(match.address, buffer);
    }
  }

  current_matches = std::move(new_matches);
}

void string_scanner::write_string_at(ADDR address, const std::string &value,
                                     E_string_encoding encoding) {
  std::vector<byte> bytes = string_to_bytes(value, encoding);
  for (size_t i = 0; i < bytes.size(); i++) {
    process_rw->write_val((byte *)(address + i), bytes[i]);
  }
}

void string_scanner::write_aob_at(ADDR address,
                                  const std::vector<byte> &bytes) {
  for (size_t i = 0; i < bytes.size(); i++) {
    process_rw->write_val((byte *)(address + i), bytes[i]);
  }
}
