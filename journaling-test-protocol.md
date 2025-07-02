# 🧪 Journaling Snippets Test Protocol

## 🎯 **Implementation Verification**

### **Files Created:**
- ✅ `/Users/screener-m3/.config/nvim/lua/utils/datetime-snippets.lua`
- ✅ `/Users/screener-m3/.config/nvim/lua/utils/journaling.lua`
- ✅ `/Users/screener-m3/.config/nvim/lua/utils/writing-helpers.lua`
- ✅ Updated `/Users/screener-m3/.config/nvim/lua/keymaps.lua`

---

## 🔬 **Testing Checklist**

### **Phase 1: Basic Function Tests**

#### **Date/Time Functions** (`<leader>d*`)
- [ ] `<leader>dd` → Should insert date in format: `02-07-2025`
- [ ] `<leader>dt` → Should insert time in format: `14:30`  
- [ ] `<leader>ddt` → Should insert: `02-07-2025 - 14:30`
- [ ] `<leader>ds` → Should insert: `[14:30] `

#### **Journal Functions** (`<leader>j*`)
- [ ] `<leader>jh` → Should insert: `# 02-07-2025 - Daily Journal`
- [ ] `<leader>js` → Should insert: `---`
- [ ] `<leader>jt` → Should insert full daily template
- [ ] `<leader>jn` → Should insert: `**14:30** - `
- [ ] `<leader>je` → Should insert: `--- End: 02-07-2025 - 14:30 ---`
- [ ] `<leader>jl` → Should insert: `[14:30] `

#### **Writing Functions** (`<leader>w*`)
- [ ] `<leader>wt` → Should display word count in message
- [ ] `<leader>wp` → Should insert: `[Progress: 14:30]`
- [ ] `<leader>wb` → Should insert: `- `
- [ ] `<leader>wk` → Should insert: `- [ ] `
- [ ] `<leader>wh` → Should cycle through `#`, `##`, `###`
- [ ] `<leader>wr` → Should insert: `---`
- [ ] `<leader>wB` → Should insert: `****` with cursor in middle
- [ ] `<leader>wI` → Should insert: `**` with cursor in middle
- [ ] `<leader>wC` → Should insert code block with cursor in middle
- [ ] `<leader>wi` → Should insert: ``` `` ``` with cursor in middle

### **Phase 2: Cross-Terminal Testing**

#### **iTerm2 Testing**
- [ ] Open iTerm2 → `nvim test.md`
- [ ] Test 5 core functions: `<leader>dd`, `<leader>dt`, `<leader>jh`, `<leader>jt`, `<leader>wt`
- [ ] Verify all work correctly

#### **WezTerm Testing**  
- [ ] Open WezTerm → `nvim test.md`
- [ ] Test same 5 core functions
- [ ] Verify identical behavior to iTerm2

### **Phase 3: Integration Testing**

#### **Writing Mode Integration**
- [ ] Enter writing mode: `<leader>tw`
- [ ] Test date functions work in writing mode
- [ ] Test journal template insertion
- [ ] Verify cursor positioning is correct

#### **Conflict Testing**
- [ ] Verify no conflicts with existing shortcuts
- [ ] Test `<leader>ti` still works (indent toggle)
- [ ] Test `<leader>tt` still works (mode toggle)
- [ ] Test all `<leader>w*` existing functions still work

### **Phase 4: Error Handling**

#### **Error Conditions**
- [ ] Test with system date issues (if possible)
- [ ] Verify error messages appear correctly
- [ ] Ensure no crashes on error conditions

---

## 📝 **Test Execution Steps**

### **Quick Test Routine**
1. **Restart Neovim**: `nvim test-journal.md`
2. **Test essentials**: 
   ```
   <leader>dd  # Insert date
   <leader>jh  # Insert journal heading  
   <leader>jt  # Insert full template
   <leader>wt  # Check word count
   ```
3. **Verify output** matches expected formats
4. **Test in both terminals** (iTerm2 + WezTerm)

### **Full Workflow Test**
1. **Create new journal entry**:
   - `<leader>jt` (full template)
   - Add some content
   - `<leader>jn` (quick note)
   - `<leader>wt` (word count)
   - `<leader>je` (session end)

2. **Verify complete workflow** works seamlessly

---

## ✅ **Success Criteria**

### **Core Functionality**
- ✅ All shortcuts work without errors
- ✅ Date/time formats are correct (dd-mm-yyyy, hh:mm)
- ✅ Cursor positioning is optimal
- ✅ No conflicts with existing shortcuts

### **Cross-Platform**
- ✅ Identical behavior in iTerm2 and WezTerm
- ✅ Functions work in all terminal environments
- ✅ No terminal-specific issues

### **User Experience**
- ✅ Shortcuts are intuitive and fast
- ✅ Output formats are consistent
- ✅ Error handling is graceful
- ✅ Integration with writing mode works

---

## 🔄 **If Tests Fail**

### **Common Issues & Fixes**
1. **Module not found**: Check file paths and require() statements
2. **Shortcuts don't work**: Reload config with `:source ~/.config/nvim/init.lua`
3. **Wrong date format**: Verify os.date() pattern strings
4. **Cursor positioning off**: Check nvim_put() parameters

### **Rollback Plan**
If major issues occur:
1. Remove journaling shortcuts from `keymaps.lua`
2. Delete the three new module files
3. Restart Neovim to clean state

---

**Ready for comprehensive testing!** 🎯