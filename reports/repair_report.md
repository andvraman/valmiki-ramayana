# Gloss-pair repair plan

- rows with at least one broken fragment: 3364
- broken fragments seen: 4972
- rows repaired: 2191
- rows skipped: 1173
- well-formed pairs gained: 1706

## Rules applied
- DROP: 85
- JOIN: 2042
- SPLIT: 821
- SPLIT3+: 20

## Rows skipped, by reason
- kanda 1: run-together cannot be split cleanly — 46
- kanda 1: fragment has no English — 3
- kanda 1: orphan cannot be rejoined — 2
- kanda 2: run-together cannot be split cleanly — 57
- kanda 2: fragment has no English — 2
- kanda 3: run-together cannot be split cleanly — 26
- kanda 3: orphan cannot be rejoined — 9
- kanda 3: fragment has no English — 6
- kanda 4: run-together cannot be split cleanly — 57
- kanda 4: fragment has no English — 4
- kanda 4: orphan cannot be rejoined — 2
- kanda 5: run-together cannot be split cleanly — 24
- kanda 5: fragment has no English — 6
- kanda 5: orphan cannot be rejoined — 2
- kanda 6: run-together cannot be split cleanly — 700
- kanda 6: fragment has no English — 225
- kanda 6: orphan cannot be rejoined — 1
- kanda 7: run-together cannot be split cleanly — 1

## Samples
### skipped
- `1.1.3`
  - before: REASON: run-together cannot be split cleanly
  - after : fragment: क: who? एकप्रियदर्शन: च solely delightful in  appearance  to everyone
- `1.1.26`
  - before: REASON: run-together cannot be split cleanly
  - after : fragment: the assumed form of visnuhnu
- `1.1.27`
  - before: REASON: run-together cannot be split cleanly
  - after : fragment: the assumed form of visnuhnu
- `1.1.60`
  - before: REASON: fragment has no English
  - after : fragment: god of fire
- `1.2.41`
  - before: REASON: run-together cannot be split cleanly
  - after : fragment: तस्य (महर्षे:) वाल्मीकेः to Valmiki
- `1.3.29`
  - before: REASON: run-together cannot be split cleanly
  - after : fragment: Pushpaka's दर्शनम् viewing of
- `1.4.8`
  - before: REASON: run-together cannot be split cleanly
  - after : fragment: त्रिभि: प्रमाणै: (सह) to the three measures of time (slow
- `1.4.9`
  - before: REASON: run-together cannot be split cleanly
  - after : fragment: त्रिभि: प्रमाणै: (सह) to the three measures of time (slow
### JOIN
- `1.1.4`
  - before: आत्मवान् selfrestrained, क: who?, जितक्रोध: one who has conquered anger, द्युतिमान् one who is endow
  - after : आत्मवान् selfrestrained, क: who?, जितक्रोध: one who has conquered anger, द्युतिमान् one who is endow
- `1.1.14`
  - before: स्वस्य of his own, धर्मस्य duties of a king, रक्षिता protector, स्वजनस्य च of his own subjects, रक्ष
  - after : स्वस्य of his own, धर्मस्य duties of a king, रक्षिता protector, स्वजनस्य च of his own subjects, रक्ष
- `1.1.17`
  - before: कौसल्यानन्दवर्धन: he, who is enhancing the joys of Kausalya, स: च he also, सर्वगुणोपेत:  endowed wit
  - after : कौसल्यानन्दवर्धन: he who is enhancing the joys of Kausalya, स: च he also, सर्वगुणोपेत:  endowed with
### SPLIT
- `1.1.28`
  - before: पौरै: by citizens, पित्रा दशरथेन च by his father Dasaratha also, दूरम् for a long distance, अनुगत: f
  - after : पौरै: by citizens, पित्रा दशरथेन च by his father Dasaratha also, दूरम् for a long distance, अनुगत: f
- `1.1.29`
  - before: पौरै: by citizens, पित्रा दशरथेन च by his father Dasaratha also, दूरम् for a long distance, अनुगत: f
  - after : पौरै: by citizens, पित्रा दशरथेन च by his father Dasaratha also, दूरम् for a long distance, अनुगत: f
- `1.1.35`
  - before: आर्यभावपुरस्कृत: worshipped with reverence, सुमहात्मानम् highly respectable, सत्यपराक्रमम्  truthful
  - after : आर्यभावपुरस्कृत: worshipped with reverence, सुमहात्मानम् highly respectable, सत्यपराक्रमम्  truthful
### SPLIT3+
- `1.10.12`
  - before: ब्रह्मन् O Brahman, त्वं क: who are you? किं वर्तसे how are you subsisting? त्वम् you, एक: alone, वि
  - after : ब्रह्मन् O Brahman, त्वं क: who are you?, किं वर्तसे how are you subsisting?, त्वम् you, एक: alone, 
- `2.12.94`
  - before: हन्त What a calamity, मम अमित्रे O enemy of mine अनार्ये O wicked one कैकयि Kaikeyi, सकामा with desi
  - after : हन्त What a calamity, मम अमित्रे O enemy of mine, अनार्ये O wicked one, कैकयि Kaikeyi, सकामा with de
- `2.12.95`
  - before: हन्त What a calamity, मम अमित्रे O enemy of mine अनार्ये O wicked one कैकयि Kaikeyi, सकामा with desi
  - after : हन्त What a calamity, मम अमित्रे O enemy of mine, अनार्ये O wicked one, कैकयि Kaikeyi, सकामा with de
### DROP
- `1.18.49`
  - before: महामुने O Great sage, अमृतस्य nectar's, सम्प्राप्ति: obtaining, यथा like, अनूदके in a parched land व
  - after : महामुने O Great sage, अमृतस्य nectar's, सम्प्राप्ति: obtaining, यथा like, अनूदके in a parched land, 
- `1.18.50`
  - before: महामुने O Great sage, अमृतस्य nectar's, सम्प्राप्ति: obtaining, यथा like, अनूदके in a parched land व
  - after : महामुने O Great sage, अमृतस्य nectar's, सम्प्राप्ति: obtaining, यथा like, अनूदके in a parched land, 
- `1.37.7`
  - before: यस्याम् in this, हुताशन: fire god, अरिन्दमम् destroyer of enemies,, देवानाम् for devatas, सेनापतिम् 
  - after : यस्याम् in this, हुताशन: fire god, अरिन्दमम् destroyer of enemies, देवानाम् for devatas, सेनापतिम् a
