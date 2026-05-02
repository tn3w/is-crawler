# Snippets

Copy-paste single-file gists. No deps. Stdlib only.

| File                                           | What                                                                  |
| ---------------------------------------------- | --------------------------------------------------------------------- |
| [is_crawler_minimal.py](is_crawler_minimal.py) | 14-token `in` check. ~75% crawler recall, 0% browser FP. Fastest.     |
| [is_crawler_full.py](is_crawler_full.py)       | Keywords + URL/email + browser-signature negation. Higher recall.     |
| [crawler_name.py](crawler_name.py)             | Bot name from `(compatible; X/...)` or leading product.               |
| [crawler_version.py](crawler_version.py)       | Paired version.                                                       |
| [crawler_url.py](crawler_url.py)               | Embedded `+http(s)://` URL and `contact: a@b.c` email.                |
| [parse_user_agent.py](parse_user_agent.py)     | Browser/engine/OS/device dataclass.                                   |
| [detect_os.py](detect_os.py)                   | OS + version (Windows/iOS/macOS/Android/Linux).                       |
| [detect_engine.py](detect_engine.py)           | Blink/AppleWebKit/Gecko/Trident/Presto/KHTML.                         |
| [is_mobile.py](is_mobile.py)                   | Mobile + tablet flags.                                                |
| [fcrdns.py](fcrdns.py)                         | Forward-confirmed reverse DNS verify (Googlebot et al).               |
| [robots_txt.py](robots_txt.py)                 | Build + parse robots.txt.                                             |
| [db_reader.py](db_reader.py)                   | Load `crawler-user-agents.json`, 3-char prefix bucket → ~1 µs lookup. |
| [tests.py](tests.py)                           | Pytest suite: basic accuracy + fixture pass rates.                    |

Drop into your project. Edit token lists to taste.

```bash
cd snippets && python -m pytest tests.py -p no:cacheprovider --no-cov
```
