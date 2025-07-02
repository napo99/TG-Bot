# 📝 Journaling & Writing Shortcuts Reference

## 🎯 **Quick Start Guide**

### **Essential Date/Time Shortcuts**
| Shortcut | Output | Usage |
|----------|---------|-------|
| `<leader>dd` | `02-07-2025` | Insert current date |
| `<leader>dt` | `14:30` | Insert current time |
| `<leader>ddt` | `02-07-2025 - 14:30` | Insert date & time |
| `<leader>ds` | `[14:30] ` | Insert timestamp for notes |

### **Journal Template Shortcuts**
| Shortcut | Function | Usage |
|----------|----------|-------|
| `<leader>jh` | Journal heading | `# 02-07-2025 - Daily Journal` |
| `<leader>jt` | Full daily template | Complete journal structure |
| `<leader>jn` | Quick note | `**14:30** - ` |
| `<leader>js` | Separator | `---` |
| `<leader>je` | Session end | `--- End: 02-07-2025 - 14:30 ---` |
| `<leader>jl` | Log timestamp | `[14:30] ` |

### **Writing Productivity Shortcuts**
| Shortcut | Function | Usage |
|----------|----------|-------|
| `<leader>wt` | Word count | Display current word/character count |
| `<leader>wp` | Progress marker | `[Progress: 14:30]` |
| `<leader>wb` | Bullet point | `- ` |
| `<leader>wk` | Task checkbox | `- [ ] ` |
| `<leader>wh` | Cycle headings | `#`, `##`, `###` |
| `<leader>wr` | Horizontal rule | `---` |

### **Markdown Formatting Shortcuts**
| Shortcut | Function | Output |
|----------|----------|--------|
| `<leader>wB` | Bold markers | `**\|**` (cursor between) |
| `<leader>wI` | Italic markers | `*\|*` (cursor between) |
| `<leader>wC` | Code block | ```\n\|\n``` (cursor in middle) |
| `<leader>wi` | Inline code | `\|\` (cursor between) |

---

## 🚀 **Practical Usage Examples**

### **Daily Journal Workflow**
1. **Start new journal**: `<leader>jt` (creates full template)
2. **Add quick notes**: `<leader>jn` (timestamped entries)
3. **Check progress**: `<leader>wt` (word count)
4. **End session**: `<leader>je` (session marker)

### **Note-Taking Workflow**  
1. **Add heading**: `<leader>jh` (dated heading)
2. **Bullet points**: `<leader>wb` (quick bullets)
3. **Tasks**: `<leader>wk` (checkboxes)
4. **Timestamps**: `<leader>ds` (time references)

### **Writing Session Workflow**
1. **Progress tracking**: `<leader>wp` (time markers)
2. **Word count**: `<leader>wt` (track progress)
3. **Formatting**: `<leader>wB`, `<leader>wI` (emphasis)
4. **Structure**: `<leader>wh` (headings), `<leader>wr` (sections)

---

## 📁 **File Structure**

```
~/.config/nvim/lua/utils/
├── datetime-snippets.lua  # Date/time functions
├── journaling.lua         # Journal templates
└── writing-helpers.lua    # Writing productivity
```

---

## 🔧 **Customization Options**

### **Date Format Customization**
Edit `/Users/screener-m3/.config/nvim/lua/utils/datetime-snippets.lua`:
```lua
-- Current: "%d-%m-%Y" (02-07-2025)
-- Options: "%Y-%m-%d" (2025-07-02)
--          "%m/%d/%Y" (07/02/2025)
--          "%B %d, %Y" (July 02, 2025)
```

### **Journal Template Customization**
Edit `/Users/screener-m3/.config/nvim/lua/utils/journaling.lua`:
```lua
-- Modify the template array to add/remove sections
local template = {
  "# " .. date .. " - Daily Journal",
  "## Your Custom Section",
  "- Your custom content",
  -- ... customize as needed
}
```

### **Shortcut Customization**
Edit `/Users/screener-m3/.config/nvim/lua/keymaps.lua`:
```lua
-- Change any shortcut by modifying the first parameter
vim.keymap.set('n', '<leader>dd', datetime.insert_date, ...)
--                   ^^^^^^^^^^^^ Change this shortcut
```

---

## 🧪 **Testing Instructions**

### **Test All Functions**
1. **Open Neovim**: `nvim test.md`
2. **Test date functions**: `<leader>dd`, `<leader>dt`, `<leader>ddt`
3. **Test journal functions**: `<leader>jh`, `<leader>jt`, `<leader>jn`
4. **Test writing helpers**: `<leader>wt`, `<leader>wb`, `<leader>wk`
5. **Test formatting**: `<leader>wB`, `<leader>wI`, `<leader>wC`

### **Cross-Terminal Testing**
- ✅ **iTerm2**: All shortcuts work
- ✅ **WezTerm**: All shortcuts work
- ✅ **Terminal.app**: All shortcuts work
- ✅ **tmux sessions**: All shortcuts work

---

## 🆘 **Troubleshooting**

### **If shortcuts don't work:**
1. **Reload config**: `:source ~/.config/nvim/init.lua`
2. **Check conflicts**: `:verbose map <leader>dd`
3. **Verify modules**: `:lua print(require('utils.datetime-snippets'))`

### **If date/time is wrong:**
- Check system time: `date` in terminal
- Verify timezone settings

### **If cursor positioning is off:**
- Functions automatically position cursor optimally
- Use normal Neovim cursor movement if needed

---

## 📈 **Benefits**

### **Productivity Gains**
- ⚡ **Instant timestamps**: No manual typing
- 📝 **Consistent formatting**: Standardized journal structure  
- 🔄 **Workflow automation**: Templates reduce setup time
- 📊 **Progress tracking**: Built-in word counting and time markers

### **Writing Quality**
- 🎯 **Focus**: Less time on formatting, more on content
- 📋 **Organization**: Structured templates and sections
- ⏰ **Time tracking**: Natural session and progress markers
- ✍️ **Consistency**: Standardized date/time formats

---

**Ready to enhance your journaling and writing workflow!** 🚀