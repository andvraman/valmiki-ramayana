# Uttara Kanda alignment audit — Gita Press `.txt` vs `data_7.json` (Tokunaga)

**Report only — nothing modified.** Half-line = pada, split on danda; compared on normalised Sanskrit (verse stamps, dandas, avagraha, whitespace stripped; no sandhi).

## Task 1 — parse coverage

- Both sides cover **sargas 1–111** (111 each). No sarga missing on either side.
- **0 hard-unparseable** blocks.
- **Low parse confidence (manual review):** [34] — half-line counts differ by >4 (ragged half-verse layout the parser handles imperfectly).

## Summary

- **47** sargas identical (Sanskrit half-lines match exactly).
- **25** sargas differ only by variant *readings* (same padas, different spelling).
- **39** sargas have a half-line wholly **missing / duplicated** on one side.
- Totals: **31** half-lines in .txt absent from data_7.json (3a); **42** in data_7.json absent from .txt (3b, incl. duplicates); **84** variant readings.

## 3a/3b — structural divergences (missing half-lines & duplicates)

Only true insert/delete shown (variant readings excluded). `[low-conf]` marks a ragged-layout sarga.

### sarga 1  (txt 83 / dj 82 half-lines, sim 0.994)
- **3c** first row-pairing divergence: .txt v3 ↔ data_7 sh3 [delete]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v3: `अगस्त्योऽत्रिश्र्च भगवान् सुमुखो विमुखस्तथा`

### sarga 3  (txt 72 / dj 72 half-lines, sim 0.944)
- **3c** first row-pairing divergence: .txt v16 ↔ data_7 sh15 [replace]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v23: `निवासनं न मे देवो विदधे स प्रजापतिः`

### sarga 6  (txt 142 / dj 141 half-lines, sim 0.975)
- **3c** first row-pairing divergence: .txt v38 ↔ data_7 sh39 [delete]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v38: `दुःखं नारायणं जेतुं यो नो हन्तुमिहेच्छति`

### sarga 10  (txt 98 / dj 99 half-lines, sim 0.995)
- **3c** first row-pairing divergence: .txt v49 ↔ data_7 sh25 [insert]; re-converges: True
- **3b** in data_7.json, MISSING from .txt — sh25: `भविष्यति न सन्देहो मद्वरात्तवराक्षस`

### sarga 13  (txt 82 / dj 82 half-lines, sim 0.988)
- **3c** first row-pairing divergence: .txt v31 ↔ data_7 sh27 [insert]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v31: `पैङ्गल्यं यदवाप्तं हि देव्या रूपनिरीक्षणात्`
- **3b** in data_7.json, MISSING from .txt — sh27: `पैङ्गल्यं यदवाप्तं हि देव्या रूपनिरीक्षणात्`

### sarga 15  (txt 89 / dj 90 half-lines, sim 0.972)
- **3c** first row-pairing divergence: .txt v15 ↔ data_7 sh15 [replace]; re-converges: True
- **3b** in data_7.json, MISSING from .txt — sh25: `देवं चेष्टयते सर्वं हतो दैवेन हन्यते`

### sarga 16  (txt 99 / dj 100 half-lines, sim 0.985)
- **3c** first row-pairing divergence: .txt v18 ↔ data_7 sh18 [replace]; re-converges: True
- **3b** in data_7.json, MISSING from .txt — sh32: `अथ ते मन्त्रिणस्तस्य विक्रोशन्तमथाब्रुवन्`

### sarga 17  (txt 88 / dj 88 half-lines, sim 0.966)
- **3c** first row-pairing divergence: .txt v14 ↔ data_7 sh8 [delete]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v14: `अब्रवीद्  विधिवत कृत्वा तस्यातिथ्यं तपोधना`

### sarga 18  (txt 71 / dj 73 half-lines, sim 0.972)
- **3c** first row-pairing divergence: .txt v12 ↔ data_7 sh12 [insert]; re-converges: True
- **3b** in data_7.json, MISSING from .txt — sh12: `नाधर्मसहितं श्लाध्यं तल्लोकं प्रतिसंहितम्`
- **3b** in data_7.json, MISSING from .txt — sh12: `कर्म दौरात्म्यकं कृत्वा श्लाघ्यसे भ्रातृनिर्जयात्`

### sarga 19  (txt 64 / dj 66 half-lines, sim 0.969)
- **3c** first row-pairing divergence: .txt v17 ↔ data_7 sh16 [insert]; re-converges: True
- **3b** in data_7.json, MISSING from .txt — sh16: `नश्यति स्म बलं तत्र हव्यं हुतमिवानले`

### sarga 20  (txt 67 / dj 67 half-lines, sim 0.97)
- **3c** first row-pairing divergence: .txt v1 ↔ data_7 sh1 [delete]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v1: `रावण का संधुक्षण (उकसाना)`
- **3b** in data_7.json, MISSING from .txt — sh6: `श्रुत्वा चानन्तरं कार्यं त्वया राक्षससत्तम`

### sarga 26  (txt 120 / dj 123 half-lines, sim 0.971)
- **3c** first row-pairing divergence: .txt v6 ↔ data_7 sh6 [insert]; re-converges: True
- **3b** in data_7.json, MISSING from .txt — sh6: `आरग्वधैस्तमालैश्च प्रियालवकुलैरपि`
- **3b** in data_7.json, MISSING from .txt — sh8: `भिरुद्भासितवनान्तरे`
- **3b** in data_7.json, MISSING from .txt — sh42: `अस्मि यदवोचस्त्वमेकपत्नीष्वयं क्रमः`

### sarga 27  (txt 104 / dj 103 half-lines, sim 0.976)
- **3c** first row-pairing divergence: .txt v22 ↔ data_7 sh22 [insert]; re-converges: True
- **3b** in data_7.json, MISSING from .txt — sh22: `यामि ज्ञात्वा कालमुपागतम्`

### sarga 30  (txt 108 / dj 111 half-lines, sim 0.959)
- **3c** first row-pairing divergence: .txt v9 ↔ data_7 sh9 [insert]; re-converges: True
- **3b** in data_7.json, MISSING from .txt — sh9: `चतुष्पदां खेचराणामन्येषां वा महौजसाम्`
- **3b** in data_7.json, MISSING from .txt — sh9: `वृक्षगुल्मक्षुपलतातृणोपलमहीभृताम्`
- **3b** in data_7.json, MISSING from .txt — sh10: `सर्वे ऽपि जन्तवो ऽन्योन्यं भेतव्ये सति बिभ्यति`
- **3b** in data_7.json, MISSING from .txt — sh10: `अतो ऽत्र लोके सर्वेषां सर्वस्माच्च भवेद्भयम्`
- **3b** in data_7.json, MISSING from .txt — sh13: `्वं हि कस्यचित्प्राणिनो भुवि`

### sarga 32  (txt 147 / dj 148 half-lines, sim 0.99)
- **3c** first row-pairing divergence: .txt v29 ↔ data_7 sh29 [insert]; re-converges: True
- **3b** in data_7.json, MISSING from .txt — sh29: `चः श्रुत्वा मन्त्रिणो ऽथार्जुनस्य ते`

### sarga 34 `[low-conf]`  (txt 85 / dj 92 half-lines, sim 0.96)
- **3c** first row-pairing divergence: .txt v5 ↔ data_7 sh5 [insert]; re-converges: True
- **3b** in data_7.json, MISSING from .txt — sh5: `राक्षसेन्द गतो वाली यस्ते प्रतिबलो भवेत्`
- **3b** in data_7.json, MISSING from .txt — sh6: `इमं मुहूर्तमायाति वाली तिष्ठ मुहूर्तकम्`
- **3b** in data_7.json, MISSING from .txt — sh15: `न चिन्तयति तं वाली रावणं पापनिश्चयम्`
- **3b** in data_7.json, MISSING from .txt — sh18: `इत्येवं मतिमास्थाय वाली कर्णमुपाश्रितः`
- **3b** in data_7.json, MISSING from .txt — sh20: `पराङ्मुखो ऽपि जग्राह वाली सर्पमिवाण्डजः`
- **3b** in data_7.json, MISSING from .txt — sh22: `जहार रावणं वाली पवनस्तोयदं यथा`
- **3b** in data_7.json, MISSING from .txt — sh28: `पश्चिमं सागरं वाली ह्याजगाम सरावणः`

### sarga 35  (txt 131 / dj 130 half-lines, sim 0.989)
- **3c** first row-pairing divergence: .txt v52 ↔ data_7 sh52 [replace]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v57: `वायुसंरोधजं दुःखमिदं नो नुद दुःखहन्`

### sarga 36  (txt 126 / dj 124 half-lines, sim 0.952)
- **3c** first row-pairing divergence: .txt v7 ↔ data_7 sh7 [replace]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v21: `दीर्घायुश्च महात्मा च इति ब्रह्माब्रवीद्वचः`
- **3a** in .txt, MISSING from data_7.json — v21: `सर्वेषां ब्रह्मदण्डानामवध्योऽयं भविष्यति`
- **3a** in .txt, MISSING from data_7.json — v50: `गजो गवाक्षो गवयः सुदंष्ट्रो मैन्दः प्रभो ज्योतिमुखो नलश्च`
- **3a** in .txt, MISSING from data_7.json — v50: `एते च ऋक्षाः सह वानरेन्द्रैस्त्वत्कारणाद् राम सुरैर्हि सृष्टाः`
- **3b** in data_7.json, MISSING from .txt — sh19: `सर्वेषां ब्रह्मदण्डानामवध्यो ऽयं भविष्यति`
- **3b** in data_7.json, MISSING from .txt — sh19: `दीर्घायुश्च महात्मा च इति ब्रह्माब्रवीद्वचः`
- **3b** in data_7.json, MISSING from .txt — sh39: `पित्र्ये पदे कृतो वाली सुग्रीवो वालिनः पदे`

### sarga 38  (txt 67 / dj 66 half-lines, sim 0.992)
- **3c** first row-pairing divergence: .txt v1 ↔ data_7 sh1 [delete]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v1: `श्रीरामका जनक, युधाजित्, प्रतर्दन तथा अन्य राजाओंको विदा करना`

### sarga 40  (txt 62 / dj 59 half-lines, sim 0.909)
- **3c** first row-pairing divergence: .txt v6 ↔ data_7 sh5 [delete]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v6: `ऋक्षराजं च दुर्धर्षं जाम्बवन्तं महाबलम्`
- **3a** in .txt, MISSING from data_7.json — v23: `शेषस्येहोपकारणां भवाम ऋणिनो वयम्`
- **3a** in .txt, MISSING from data_7.json — v24: `मदङ्गे जीर्णतां यातु यत् त्वयोपकृतं कपे`
- **3b** in data_7.json, MISSING from .txt — sh22: `लोके च मामिका`

### sarga 46  (txt 68 / dj 67 half-lines, sim 0.933)
- **3c** first row-pairing divergence: .txt v1 ↔ data_7 sh1 [delete]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v1: `लक्ष्मण का सीता को रथपर बिठाकर गङ्गा के तटपर ले जाना`

### sarga 51  (txt 60 / dj 61 half-lines, sim 0.975)
- **3c** first row-pairing divergence: .txt v5 ↔ data_7 sh4.1 [insert]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v12: `तया दत्ताभयास्तत्र न्यवसन्नभयास्तदा`
- **3b** in data_7.json, MISSING from .txt — sh4.1: `तौ मुनी तापसश्रेष्ठौ विनीतो ह्यभिवादयत्`
- **3b** in data_7.json, MISSING from .txt — sh4.1: `स ताभ्यां पूजितो राजा स्वागतेनासनेन च`

### sarga 57  (txt 43 / dj 41 half-lines, sim 0.976)
- **3c** first row-pairing divergence: .txt v21 ↔ data_7 shNone [delete]; re-converges: False
- **3a** in .txt, MISSING from data_7.json — v21: `इति सर्वमशेषतो मया कथितं संभवकारणं तु सौम्य`
- **3a** in .txt, MISSING from data_7.json — v21: `नृपपुङ्गवशापजं द्विजस्य द्विजशापाच्च यदद्भुतं नृपस्य`

### sarga 59  (txt 47 / dj 46 half-lines, sim 0.989)
- **3c** first row-pairing divergence: .txt v1 ↔ data_7 sh1 [delete]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v1: `पूरु का जरा ग्रहण करना, यदु को शाप तथा पूरु का राज्याभिषेक`

### sarga 61  (txt 49 / dj 51 half-lines, sim 0.98)
- **3c** first row-pairing divergence: .txt v5 ↔ data_7 sh5 [insert]; re-converges: True
- **3b** in data_7.json, MISSING from .txt — sh5: `बहुवर्षसहस्राणि रुद्रप्रीत्या ऽकरोत्तपः`
- **3b** in data_7.json, MISSING from .txt — sh6: `रुद्रः प्रीतो ऽभवत्तस्मै वरं दातुं ययौ च सः`

### sarga 70  (txt 36 / dj 35 half-lines, sim 0.986)
- **3c** first row-pairing divergence: .txt v1 ↔ data_7 sh1 [delete]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v1: `देवताओं का शत्रुघ्न को वर देना तथा शत्रुघ्न का मधुपुरी (शूरसेना) को बसाना`

### sarga 73  (txt 39 / dj 38 half-lines, sim 0.987)
- **3c** first row-pairing divergence: .txt v1 ↔ data_7 sh1 [delete]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v1: `मृत बालक को लेकर वृद्ध ब्राह्मण का राजद्वारपर विलाप करना`

### sarga 76  (txt 105 / dj 104 half-lines, sim 0.995)
- **3c** first row-pairing divergence: .txt v1 ↔ data_7 sh1 [delete]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v1: `शम्बूक-वध, ब्राह्मणपुत्र का पुनर्जीवन तथा अगस्त्य जी का श्रीराम को दिव्य आभूषण देना`

### sarga 78  (txt 58 / dj 61 half-lines, sim 0.975)
- **3c** first row-pairing divergence: .txt v16 ↔ data_7 sh16 [insert]; re-converges: True
- **3b** in data_7.json, MISSING from .txt — sh16: `तृप्तिर्न ते ऽस्ति सूक्ष्मा ऽपि वने सत्वनिषेविते`
- **3b** in data_7.json, MISSING from .txt — sh16: `पुरा तु भिक्षमाणाय भिक्षा वै यतये नृप`
- **3b** in data_7.json, MISSING from .txt — sh16: `न हि दत्ता त्वयेन्द्राभ यस्मादतिथये ऽपि वै`

### sarga 83  (txt 42 / dj 41 half-lines, sim 0.988)
- **3c** first row-pairing divergence: .txt v1 ↔ data_7 sh1 [delete]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v1: `श्रीराम का राजसूय यज्ञ का विचार तथा भरत के समझानेपर उससे निवृत्त होना`

### sarga 95  (txt 35 / dj 35 half-lines, sim 0.971)
- **3c** first row-pairing divergence: .txt v1 ↔ data_7 sh1 [delete]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v1: `श्रीराम का कुश-लव को सीता का पुत्र जानकर वाल्मीकि जी के पास दूत भेजना`
- **3b** in data_7.json, MISSING from .txt — sh4: `परिषदो मध्ये रामो वचनमब्रवीत्`

### sarga 98  (txt 55 / dj 56 half-lines, sim 0.973)
- **3c** first row-pairing divergence: .txt v10 ↔ data_7 sh10 [replace]; re-converges: True
- **3b** in data_7.json, MISSING from .txt — sh18: `आदिकाव्यमिदं राम त्वयि सर्वं प्रतिष्ठितम्`

### sarga 99  (txt 41 / dj 40 half-lines, sim 0.988)
- **3c** first row-pairing divergence: .txt v1 ↔ data_7 sh1 [delete]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v1: `श्रीराम का यज्ञपूर्वक दीर्घकाल राज्य करना तथा कौसल्या आदि माताओं का स्वर्गगमन`

### sarga 100  (txt 52 / dj 51 half-lines, sim 0.99)
- **3c** first row-pairing divergence: .txt v1 ↔ data_7 sh1 [delete]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v1: `युधाजित् का संदेश तथा भरत का तक्ष-पुष्कल सहित गन्धर्वदेश पर विजययात्रा को प्रस्थान`

### sarga 104  (txt 40 / dj 39 half-lines, sim 0.987)
- **3c** first row-pairing divergence: .txt v1 ↔ data_7 sh1 [delete]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v1: `काल का ब्रह्मा जी का संदेश सुनाना तथा श्रीराम का स्वधाम लौटने को स्वीकार करना`

### sarga 106  (txt 37 / dj 36 half-lines, sim 0.986)
- **3c** first row-pairing divergence: .txt v1 ↔ data_7 sh1 [delete]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v1: `श्रीराम का लक्ष्मण का परित्याग तथा लक्ष्मण का सशरीर स्वर्गगमन`

### sarga 108  (txt 77 / dj 76 half-lines, sim 0.993)
- **3c** first row-pairing divergence: .txt v37 ↔ data_7 sh38 [delete]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v37: `यावत्कलिश्च सम्प्राप्तस्तावज्जीवत सर्वदा`

### sarga 109  (txt 45 / dj 44 half-lines, sim 0.989)
- **3c** first row-pairing divergence: .txt v1 ↔ data_7 sh1 [delete]; re-converges: True
- **3a** in .txt, MISSING from data_7.json — v1: `श्रीराम का सर्वजनसहित महाप्रस्थान`

### sarga 111  (txt 49 / dj 53 half-lines, sim 0.961)
- **3c** first row-pairing divergence: .txt v16 ↔ data_7 sh15 [insert]; re-converges: True
- **3b** in data_7.json, MISSING from .txt — sh15: `आदिकाव्यमिदं त्वार्षं पुरा वाल्मीकिना कृतम्`
- **3b** in data_7.json, MISSING from .txt — sh27: `इत्युत्तरकाण्डः समाप्तः`
- **3b** in data_7.json, MISSING from .txt — sh28: `इत्यार्षे श्रीमद्वाल्मीकीये आदिकाव्ये श्रीमद्रामायणं सम्पूर्णम्`
- **3b** in data_7.json, MISSING from .txt — sh29: `श्रीसीतारामचन्द्रार्पणमस्तु`

## Variant readings (spelling/word differences, same pada position)

Count per sarga; these are recension spelling differences, not misalignment.

| sarga | variants | example (.txt → data_7) |
|--:|--:|---|
| 2 | 1 | `कुम्भयोनिर्महातेजा राममेतदुवाच ह` → `कुम्भयोनिर्मिहातेजा राममेतदुवाच ह` |
| 3 | 4 | `भगवँल्लोकपालत्वमिच्छेयं लोकरक्षणम्` → `भगवँल्लोकपालत्वमिच्छेयं वित्तरक्षण` |
| 4 | 2 | `स कालभगिनीं कन्यां भयां नाम महाभया` → `स कालभगिनीं कन्यां भयां नाम भयावहा` |
| 5 | 4 | `सत्यार्जवशमोपेतैस्तपोभिर्भुवि दुर्` → `सत्यार्जवशमोपेतैस्तपोभिरतिदुष्करैः` |
| 6 | 3 | `राक्षसानामुपरि खे भ्रमते कालवत्` → `राक्षसानामुपरि खे भ्रमते ऽलातचक्रव` |
| 7 | 1 | `शलभा इव केदारं मशका इव पावकम्` → `शलभा इव केदारं मशका इव पर्वतम्` |
| 8 | 2 | `पराङ्मुखवधं पापं यः करोति सुरेश्र्` → `पराङ्मुखवधं पापं यः करोत्यसुरेतरः` |
| 11 | 1 | `प्रत्युवाच प्रहस्तं तं वाक्यं वाक्` → `प्रत्युवाच प्रहस्तं तं वाक्यं वाक्` |
| 15 | 2 | `सन्नादः सुमहान्राजंस्तस्मिन्शैलेऽभ` → `सन्नादः सुमहान्राजंस्तस्मिन्शैले ऽ` |
| 16 | 1 | `नखदंष्ट्रायुधाः क्रूराः मनःसम्पातर` → `नखदंष्ट्रायुधाः क्रूरा मनःसम्पातरं` |
| 17 | 3 | `वै भोगेन च बलेन च मा मैवमिति सा कन` → `वै भोगेन च बलेन च` |
| 18 | 1 | `यथान्ये विविधै रोगै पीड्यन्ते प्रा` → `यथान्ये विविधै रोगै; पीड्यन्ते प्र` |
| 19 | 2 | `यदि दत्तं यदि हुतं यदि मे सुकृतं त` → `यदि दत्तं यदि हुतं यदि मे सुकृतं त` |
| 20 | 1 | `हत एव ह्ययं लोको यदा मृत्युवशं गतः` → `हत एव ह्ययं लोको यदा मृत्युवशं गतः` |
| 21 | 1 | `तिष्ठ तिष्ठेति तानुक्त्वा तच्चापं ` → `तिष्ठ तिष्ठेति तानुक्त्वा तच्चापं ` |
| 22 | 1 | `ततो महाशक्तिशरैः पात्यमानैर्महोरसि` → `ततो महाशक्तिशरैः पात्यमानैर्महोरसि` |
| 23 | 1 | `रावणं त्वब्रवीन्मन्त्री प्रहस्तो प` → `रावणं त्वब्रवीन्मन्त्री प्रहस्तो (` |
| 25 | 3 | `राजसूयस्तथा यज्ञो गोमेधो वैष्णवस्त` → `राजसूयस्तथा यज्ञो गोमेधो वैष्ववस्त` |
| 26 | 2 | `सर्वाप्सरोवरा रम्भा दपूर्णचन्द्रनि` → `सर्वाप्सरोवरा रम्भा दिव्यपुष्पविभू` |
| 27 | 3 | `सैन्यैः परिवृतो हृष्टैर्नानाप्रहरण` → `तथा ऽ ऽदित्यौ महावीर्यौ त्वष्टा पू` |
| 29 | 3 | `तच्छ्रुत्वा रावणेर्वाक्यं शुक्रहीन` → `तच्छ्रुत्वा रावणेर्वाक्यं स्वस्थचे` |
| 30 | 3 | `स तया सह धर्मात्मा रमते स्म महामुन` → `सङ्क्रुद्धस्त्वं हि धर्मात्मन् गत्` |
| 32 | 1 | `क्रीडमानाय कथितं पुरुषैर्र्भ्हयविह` → `क्रीडमानाय कथितं पुरुषैर्द्वाररक्ष` |
| 35 | 1 | `वायुप्रकोपात् त्रैलोक्यं निरयस्थमि` → `वायुप्रकोपात्ऺत्रैलोक्यं निरयस्थमि` |
| 36 | 3 | `ततस्त्रियुग्मस्त्रिककुत् त्रिधामा ` → `ततस्त्रियुग्मस्त्रिककुत्ऺित्रधामा ` |
| 39 | 1 | `तानि रत्नानि चित्राणि रामाय समुपान` → `तानि रत्नानि चित्राणि रामाय समुपाह` |
| 40 | 4 | `ऋषभं च सुविक्रान्तं प्लवङ्गं च सुप` → `ऋषभं च सुविक्रान्तं जाम्बवन्तं महा` |
| 41 | 1 | `शुश्राव मधुरां वाणीमन्तरिक्षात् मह` → `शुश्राव मधुरां वाणीमन्तरिक्षात् प्` |
| 42 | 7 | `सीतामादाय हस्तेन मधुमैरेयकं शुचि` → `सीतामादायं हस्तेन मधुमैरेयकं शुचि` |
| 43 | 1 | `रक्षसां वशमापन्नां कथं रामो न कुत्` → `रक्षसां वशमापन्नां कथं रामो न कुत्` |
| 44 | 1 | `निवेदयामास तदा भ्रातॄन्स्वान्समुपस` → `निवेदयामास तदा भ्रातऽन्स्वान्समुपस` |
| 45 | 1 | `एवमुक्त्वा तु काकुत्स्थो बाष्पेण प` → `एवमुक्त्वा तु काकुत्स्थो बाष्पेण प` |
| 46 | 4 | `गङ्गातीरे मया देवि ऋषीणामाश्रमाञ्छ` → `गङ्गीतीरे मया देवि ऋषीणामाश्रमाञ्छ` |
| 48 | 2 | `यथाज्ञं कुरु सौमित्रे त्यज मां दुः` → `यथाज्ञं कुरु सोमित्रे त्यज मां दुः` |
| 49 | 2 | `अभिवादयामस्त्वां सर्वा उच्यतां किं` → `अभिवादयामस्त्वां सर्वा उच्यतां कि ` |
| 50 | 1 | `प्राप्स्यते च महाबाहुर्विप्रयोगं प` → `प्राप्स्यते च महाबाहुर्विप्रयोगं प` |
| 60 | 1 | `ततश्च कर्ता ह्यसि नात्र संशयो महाभ` → `ततश्च कर्ता ह्यसि नात्र संशयो महाभ` |
| 82 | 2 | `लक्ष्मणं भरतं चैव गत्वा तौ लघुविक्` → `लक्ष्मणं भरतं चैव गत्वा तौ लघुविक्` |
| 85 | 1 | `पतता वृत्रशिरसा जगत् त्रासमुपागमत्` → `पतता वृत्रशिरसा जगत्ऺत्रासमुपागमत्` |
| 98 | 1 | `नाशयिष्याम्यहं भूमिं सर्वमापो भवन्` → `नाशयिष्याम्यहं भूमिं सर्वमापो भवत्` |
| 101 | 1 | `तक्षपुष्कलोपरि टिप्पणी गन्धर्वदेशे` → `गन्धर्वदेशे रुचिरे गान्धारविषये च ` |
| 110 | 3 | `त्वामचिन्त्यं महद् भूतमक्षयं चाजरं` → `त्वामचिन्त्यं महद्भूतमक्षयं सर्वसङ` |

## Beyond Sanskrit — Hindi/English mispaired on *correct* Sanskrit

A Sanskrit-only diff cannot see this class, so these sargas show as aligned above. Where GP and Tokunaga group padas differently, the row's **Sanskrit is right** but its Hindi/English (drafted against GP divisions) belongs to a neighbour.

**Confirmed example — sarga 54** (Sanskrit aligns perfectly): the English is offset by one row — sh14 Sanskrit *"the curse was laid upon me"* carries sh15's English *"Having made that arrangement…"*; sh16 Sanskrit प्राप्तव्यान्येव carries verse 15's English *"Do not give your body to grief"*; and sh17's Hindi is a notice pointing to 54.16. Your other cited case, **51.11** (Sanskrit तच्छ्रुत्वा…, Hindi is v12's), sits just after this kanda's clearest structural break (the 51.4.1/51.5 duplicate + 51.6 split, all caught in 3a/3b above).

**This needs a separate Hindi/English-pairing pass** (compare each row's prose to its own verse) — recommended as a follow-up; it is out of scope for the Sanskrit half-line diff.

## Caveats

- A few sarga **topic headings** still leak into the Sanskrit stream when short and cue-less (e.g. sarga 20 v1 `रावण का संधुक्षण (उकसाना)`, sarga 17 v1) — treat single heading-like 3a entries at v1 as noise.
- A **3a and 3b entry with identical text** (e.g. sarga 13 `पैङ्गल्यं यदवाप्तं…`) is one half-line **repositioned**, not lost — a row-pairing shift, flagged by 3c.
- Sarga **34** is low-confidence (ragged layout, half-line gap 7).