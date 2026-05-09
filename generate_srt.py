import json

# Corrections map (original word -> corrected word, case-insensitive matching)
corrections = {
    "Накроволовка,": "Микроволновка,",
    "отъем": "нальём",
    "разулся": "раскладной",
    "склейка": "склеек",
}

def format_time(seconds):
    """Convert seconds to SRT time format HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def clean_word(word):
    """Apply corrections to a word"""
    stripped = word.strip()
    for orig, fixed in corrections.items():
        if stripped == orig or stripped.lower() == orig.lower():
            return word.replace(stripped, fixed)
    return word

with open('/Users/vas/CLAUDECODE/audio.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

srt_lines = []
idx = 1

for segment in data['segments']:
    for word_data in segment['words']:
        word = word_data['word'].strip()
        start = word_data['start']
        end = word_data['end']
        
        # Apply correction
        corrected = clean_word(word)
        
        # Add small buffer so subtitle doesn't disappear too fast
        # If duration < 0.3s, extend display to at least 0.3s
        display_end = max(end, start + 0.3)
        
        srt_lines.append(f"{idx}")
        srt_lines.append(f"{format_time(start)} --> {format_time(display_end)}")
        srt_lines.append(corrected)
        srt_lines.append("")
        idx += 1

output = '\n'.join(srt_lines)

with open('/Users/vas/CLAUDECODE/subtitles_word_by_word.srt', 'w', encoding='utf-8') as f:
    f.write(output)

print(f"Generated {idx-1} word subtitles")
print("\nFirst 20 subtitles preview:")
print('\n'.join(srt_lines[:80]))
