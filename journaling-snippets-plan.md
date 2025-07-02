# Universal Journaling Snippets - Design Document

## 🎯 **Core Requirements**
- Cross-terminal compatibility (iTerm2, WezTerm, all terminals)
- Intuitive shortcuts without conflicts
- Enhanced journaling and writing UX
- Fast, efficient text insertion

## 📅 **Date/Time Functions**

### **Primary Commands**
| Shortcut | Function | Output Example |
|----------|----------|----------------|
| `<leader>dd` | Insert date | `02-07-2025` |
| `<leader>dt` | Insert time | `14:30` |
| `<leader>ddt` | Insert date & time | `02-07-2025 - 14:30` |

### **Implementation**
```lua
-- Date/time insertion module
local datetime = {}

function datetime.insert_date()
  local date = os.date("%d-%m-%Y")
  vim.api.nvim_put({date}, 'c', true, true)
end

function datetime.insert_time()
  local time = os.date("%H:%M")
  vim.api.nvim_put({time}, 'c', true, true)
end

function datetime.insert_datetime()
  local datetime = os.date("%d-%m-%Y - %H:%M")
  vim.api.nvim_put({datetime}, 'c', true, true)
end
```

## ✍️ **Journal-Specific Functions**

### **Enhanced Journaling**
| Shortcut | Function | Output Example |
|----------|----------|----------------|
| `<leader>jh` | Journal heading | `# 02-07-2025 - Daily Journal` |
| `<leader>js` | Journal separator | `---` |
| `<leader>jt` | Daily template | Full journal template |
| `<leader>jn` | Quick note | `**14:30** - ` |
| `<leader>je` | Session end | `--- End: 02-07-2025 - 14:30 ---` |

### **Implementation**
```lua
-- Journal-specific functions
local journal = {}

function journal.insert_heading()
  local date = os.date("%d-%m-%Y")
  local heading = "# " .. date .. " - Daily Journal"
  vim.api.nvim_put({heading, ""}, 'l', true, true)
end

function journal.insert_separator()
  vim.api.nvim_put({"---"}, 'l', true, true)
end

function journal.insert_template()
  local date = os.date("%d-%m-%Y")
  local time = os.date("%H:%M")
  local template = {
    "# " .. date .. " - Daily Journal",
    "",
    "**Started:** " .. time,
    "",
    "## Morning Thoughts",
    "- ",
    "",
    "## Goals for Today",
    "- [ ] ",
    "",
    "## Notes",
    "- ",
    "",
    "## Evening Reflection",
    "- ",
    "",
    "---"
  }
  vim.api.nvim_put(template, 'l', true, true)
end

function journal.quick_note()
  local time = os.date("%H:%M")
  local note = "**" .. time .. "** - "
  vim.api.nvim_put({note}, 'c', true, true)
end

function journal.session_end()
  local datetime = os.date("%d-%m-%Y - %H:%M")
  local marker = "--- End: " .. datetime .. " ---"
  vim.api.nvim_put({marker}, 'l', true, true)
end
```

## 📝 **Writing Productivity Functions**

### **Productivity Helpers**
| Shortcut | Function | Description |
|----------|----------|-------------|
| `<leader>wt` | Word count | Display current word count |
| `<leader>wp` | Progress marker | `[Progress: 14:30]` |
| `<leader>wb` | Bullet point | `- ` |
| `<leader>wh` | Heading levels | Cycle through `#`, `##`, `###` |

### **Implementation**
```lua
-- Writing productivity functions
local writing = {}

function writing.word_count()
  local word_count = vim.fn.wordcount().words
  print("📊 Word count: " .. word_count)
end

function writing.progress_marker()
  local time = os.date("%H:%M")
  local marker = "[Progress: " .. time .. "]"
  vim.api.nvim_put({marker}, 'c', true, true)
end

function writing.bullet_point()
  vim.api.nvim_put({"- "}, 'c', true, true)
end

function writing.heading_insert()
  -- Cycle through heading levels
  local headings = {"# ", "## ", "### "}
  local current = vim.g.heading_level or 1
  local heading = headings[current]
  vim.api.nvim_put({heading}, 'c', true, true)
  vim.g.heading_level = (current % 3) + 1
end
```

## 🔧 **Conflict Analysis**

### **Current Shortcuts (Analyzed)**
- `<leader>t*` - Terminal/theme related ✅
- `<leader>w*` - Writing mode related (some available) ✅
- `<leader>d*` - **AVAILABLE** ✅
- `<leader>j*` - **AVAILABLE** ✅

### **Proposed Shortcuts (Safe)**
- ✅ `<leader>dd/dt/ddt` - No conflicts with date prefix
- ✅ `<leader>j*` - Completely available journal prefix
- ✅ `<leader>wt/wp/wb/wh` - Available within writing prefix

## 📁 **File Structure**

### **Proposed Implementation Files**
```
~/.config/nvim/lua/utils/
├── journaling.lua        # Main journaling module
├── datetime-snippets.lua # Date/time functions
└── writing-helpers.lua   # Writing productivity
```

### **Keymap Integration**
```
~/.config/nvim/lua/keymaps.lua
# Add journal shortcuts section
```

## 🧪 **Testing Protocol**

### **Cross-Terminal Testing**
1. **iTerm2 compatibility test**
2. **WezTerm compatibility test**
3. **Shortcut conflict verification**
4. **Function accuracy testing**

### **Validation Checklist**
- [ ] Date format accuracy (dd-mm-yyyy)
- [ ] Time format accuracy (hh:mm)
- [ ] No keymap conflicts
- [ ] Cross-terminal functionality
- [ ] Template insertion accuracy

## 🚀 **Next Steps**

1. **Create implementation files**
2. **Add keymap integrations**
3. **Test across terminals**
4. **Document usage**
5. **Create external validation**

---

**Ready for implementation approval and execution!**