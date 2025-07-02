# Indent Toggle Validation Test Protocol

## 🧪 **External Validation Required**

### **Issue Summary:**
- `<leader>ti` indent toggle works in **WezTerm** ✅
- `<leader>ti` indent toggle **NOT working in iTerm2** ❌
- Documentation shows it should work universally

### **Recent Fix Applied:**
- **Moved keymap outside WezTerm conditional block**
- **Made keymap universal** (should work in all terminals now)

---

## **Test Protocol for External Validation:**

### **Test 1: iTerm2 Validation**
1. **Open iTerm2**
2. **Navigate to any project directory**
3. **Open Neovim**: `nvim test_file.py` (or any file)
4. **Test keymap**: Press `<space>ti` (space + t + i)
5. **Expected result**: 
   - ✅ **Message should appear**: "📐 Indent guides: ON" or "OFF"
   - ✅ **Visual change**: Vertical indent lines should toggle on/off

### **Test 2: WezTerm Validation (confirm still works)**
1. **Open WezTerm**
2. **Navigate to same project directory**
3. **Open Neovim**: `nvim test_file.py`
4. **Test keymap**: Press `<space>ti`
5. **Expected result**: Same as iTerm2 test

### **Test 3: Cross-Terminal Consistency**
1. **Test multiple file types**:
   - Python file (`.py`)
   - Markdown file (`.md`)
   - JavaScript file (`.js`)
2. **Verify behavior is identical** in both terminals

---

## **Validation Checklist:**

### **iTerm2 Results:**
- [ ] ✅ **PASS**: `<leader>ti` shows message and toggles indent lines
- [ ] ❌ **FAIL**: No response to `<leader>ti` keypress
- [ ] ⚠️ **PARTIAL**: Message appears but no visual change

### **WezTerm Results:**
- [ ] ✅ **PASS**: `<leader>ti` works correctly (as before)
- [ ] ❌ **FAIL**: Functionality broken in WezTerm
- [ ] ⚠️ **PARTIAL**: Different behavior than before

### **Cross-Terminal Consistency:**
- [ ] ✅ **PASS**: Identical behavior in both terminals
- [ ] ❌ **FAIL**: Different behavior between terminals

---

## **If Tests Fail:**

### **iTerm2 Still Not Working:**
- Check if keymap is actually loaded: `:verbose map <leader>ti`
- Check if plugin is loaded: `:IBLToggle` (manual command)
- Check terminal environment: `:lua print(vim.env.TERM_PROGRAM)`

### **WezTerm Broken:**
- Revert changes and investigate further
- Check if moving keymap affected WezTerm functionality

### **Inconsistent Behavior:**
- Investigate plugin loading differences between terminals
- Check for terminal-specific plugin configurations

---

## **Expected Final State:**
✅ `<leader>ti` works identically in **both iTerm2 and WezTerm**  
✅ **Universal functionality** as documented  
✅ **No terminal-specific differences** for indent toggle

---

**Instructions:** Please test this thoroughly and report back with specific results for each test case.