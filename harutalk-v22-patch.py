from pathlib import Path
import re

java_path = Path('harutalk/app/src/main/java/com/harutalk/app/MainActivity.java')
s = java_path.read_text(encoding='utf-8')

needle = "        micPanel.addView(micRow, lpMatchWrap());\n\n        LinearLayout.LayoutParams micPanelLp = lpMatchWrap();"
replacement = """        micPanel.addView(micRow, lpMatchWrap());

        TextView langLock = new TextView(this);
        langLock.setText(\"자동 언어감지 OFF · 한국어 버튼은 한국어, 日本語 버튼은 일본어로 고정\");
        langLock.setTextSize(10.5f);
        langLock.setTextColor(SUBTEXT);
        langLock.setPadding(dp(2), dp(6), dp(2), 0);
        micPanel.addView(langLock, lpMatchWrap());

        LinearLayout.LayoutParams micPanelLp = lpMatchWrap();"""
assert needle in s
s = s.replace(needle, replacement, 1)

s, n = re.subn(
    r"    private void initSpeechRecognizer\(\) \{.*?\n    private void beginSpeech\(String languageTag\) \{",
    """    private void initSpeechRecognizer() {
        recreateSpeechRecognizer();
    }

    private void recreateSpeechRecognizer() {
        try {
            if (speechRecognizer != null) {
                try { speechRecognizer.destroy(); } catch (Throwable ignored) { }
                speechRecognizer = null;
            }
            if (SpeechRecognizer.isRecognitionAvailable(this)) {
                speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this);
                speechRecognizer.setRecognitionListener(this);
            } else {
                setStatus(\"음성인식 서비스를 사용할 수 없습니다\", true);
            }
        } catch (Throwable t) {
            speechRecognizer = null;
            setStatus(\"음성인식 초기화 실패\", true);
        }
    }

    private void beginSpeech(String languageTag) {""",
    s, count=1, flags=re.S)
assert n == 1

s, n = re.subn(
    r"    private void startSpeechNow\(String languageTag\) \{.*?\n    private void translateInput\(boolean koreanToJapanese\) \{",
    """    private void startSpeechNow(String languageTag) {
        currentSpeechLanguage = languageTag;
        input.setText(\"\");

        // OEM recognition services may cache the previous/default language.
        // Recreate for every session and force the button-selected locale.
        recreateSpeechRecognizer();
        if (speechRecognizer == null) {
            setStatus(languageTag.startsWith(\"ko\")
                    ? \"한국어 음성인식 서비스를 시작할 수 없습니다\"
                    : \"日本語の音声認識を開始できません\", true);
            return;
        }

        Locale forcedLocale = languageTag.startsWith(\"ko\") ? Locale.KOREA : Locale.JAPAN;
        Locale.setDefault(forcedLocale);

        Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, languageTag);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, languageTag);
        intent.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true);
        intent.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3);
        intent.putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, false);
        intent.putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, getPackageName());

        try {
            speechRecognizer.startListening(intent);
            listening = true;
            setListeningUi(true, languageTag);
            setStatus(languageTag.startsWith(\"ko\")
                    ? \"한국어 고정 · 말씀하세요…\"
                    : \"日本語固定 · 話してください…\", false);
        } catch (Throwable t) {
            listening = false;
            setListeningUi(false, languageTag);
            setStatus(languageTag.startsWith(\"ko\")
                    ? \"한국어 음성인식을 시작하지 못했습니다\"
                    : \"日本語の音声認識を開始できませんでした\", true);
        }
    }

    private void translateInput(boolean koreanToJapanese) {""",
    s, count=1, flags=re.S)
assert n == 1

old = '''        setStatus(speechErrorText(error), true);\n        if (error == SpeechRecognizer.ERROR_CLIENT || error == SpeechRecognizer.ERROR_SERVER) {\n            launchFallbackRecognizer(currentSpeechLanguage == null ? "ko-KR" : currentSpeechLanguage);\n        }'''
new = '''        String lang = currentSpeechLanguage == null ? "ko-KR" : currentSpeechLanguage;\n        String prefix = lang.startsWith("ko") ? "한국어 · " : "日本語 · ";\n        setStatus(prefix + speechErrorText(error), true);'''
assert old in s
s = s.replace(old, new, 1)

assert 'launchFallbackRecognizer(' not in s
assert 'EXTRA_LANGUAGE, languageTag' in s
assert 'Locale.setDefault(forcedLocale)' in s
assert '자동 언어감지 OFF' in s

java_path.write_text(s, encoding='utf-8')

build = Path('harutalk/app/build.gradle')
b = build.read_text(encoding='utf-8')
b = b.replace('versionCode 210', 'versionCode 220')
b = b.replace("versionName '2.1.0'", "versionName '2.2.0'")
assert "versionName '2.2.0'" in b
build.write_text(b, encoding='utf-8')

print('HaruTalk v2.2 language-lock patch applied')
