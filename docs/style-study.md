# Style study

This document gives the style parameters for a new setting of the *St Matthew Passion* of J. S. Bach (BWV 244) for one alto voice and one baroque orchestra.
The parameters come from the work of Bach, from other music for one voice of his time, and from works of later composers that use the music of Bach or the form of the Passion.
The design of the new work and the composition code use these parameters.

## Method

The study has three types of data. Each row of a table has a code for its type.

| Code | Type | Meaning |
| --- | --- | --- |
| M | Measured | The study code measured open score data. The command `make study` makes these values again. |
| R | Read | The study team read the source. The column "Source" gives the key of the source. The list of sources is at the end of this document. |
| K | Reference knowledge | The row is standard knowledge of music theory or music history. The study team did not read a source for the row. Check the row before you use it for a critical decision. |

The study measured two sets of open data:

1. The four-part chorales of Bach: 370 settings in the Humdrum format (the edition of Craig Sapp).
   Eleven of these settings are in the *St Matthew Passion*.
2. Fourteen movements of Bach as MIDI files (the edition of Nancho Alvarez):
   seven movements of the *St Matthew Passion* (five arias and two large choruses), two of the *St John Passion*, two of the Mass in B minor, one of the Magnificat, and two of the *Trauerode* (BWV 198).
   Three of these movements have an alto as a solo voice.
   For nine movements, the study also read the figures of the figured bass in the text source of the edition.

The study also read the first bars of 67 sections of the Passion (text sources on Wikimedia Commons) and the full text sources of five movements.
The table of motifs (S4) comes from these sources.
The full German text of the Passion comes from the edition of W. F. Bischof.

No open score data are available for the music of the later composers (Pärt, Lang, Shaw, Gubaidulina, and others).
Their rows come from encyclopedia articles and from the notes of the composers.

## Main results

The work of Bach:

1. The Passion has three layers of text: the Gospel story (43 sections of recitative and 18 choruses of the crowd), the poems (15 arias and 11 recitatives with instruments), and the chorales (12 plain settings and 4 large choruses).
2. The work starts in E minor and ends in C minor.
   The Passion chorale comes five times: in E major, E-flat major, D major, D minor to F major, and A minor.
   The last setting, after the death of Jesus, ends on the dominant and not on the key note.
   Its bass has the largest share of semitone moves of these five settings (37.5 percent).
3. The alto of Bach: in three arias the lowest note is A3 and the highest note is E5.
   The middle of the voice is A4, and the voice is between C-sharp 4 and D5 for 90 percent of the time.
   Semitones and whole tones are 72 to 75 percent of the moves. Sixths and larger leaps are 2 to 6 percent: these are the calls ("Erbarme dich" starts with a minor sixth up).
4. In an aria, the voice sings for 50 to 60 percent of the time. The solo instrument is its partner and has about two times as many notes: 2.2 notes for each quarter note (the violin of "Erbarme dich") against 0.9 (the alto).
5. The arias and choruses of Bach are much more dissonant than his plain chorales.
   A chord with a semitone clash sounds for 7 percent of the chord time in the chorales, for 13 to 28 percent in the arias, and for 42 to 58 percent in three of the large choruses.
   One bar has 7.3 different pitch classes (middle value of 14 movements).
6. The bass is frequently a pulse: 59 to 71 percent of the bass moves are repeated notes in "Erbarme dich", in the Crucifixus, and in the opening chorus of the *St John Passion*.
   That chorus holds one bass note for 48 quarter notes.
   In the Crucifixus, 21 percent of the bass moves are semitones: the bass goes down by semitones again and again.
7. The most frequent figure of the figured bass is the 6 (19 percent of all figures). Then come 6 4, 6 5, the 7 with a raised third, 5, and 7.

Other works:

8. Music for one alto and a small baroque orchestra has a long history: Vivaldi (*Stabat Mater*, *Nisi Dominus*), Bach (the cantatas BWV 54 and BWV 170), and in the present time Caroline Shaw (*Is a Rose*, for a mezzo-soprano and an orchestra of period instruments).
9. David Lang (*the little match girl passion*) keeps the format of the *St Matthew Passion* in 15 numbers and 35 minutes: story numbers and response numbers in turn. This is the scale of the new work.
10. Arvo Pärt (*Passio*) makes the rhythm from the text: the punctuation gives the length of each syllable. Each person of the story has a pitch centre.
11. Knut Nystedt (*Immortal Bach*) lets each voice sing one chorale phrase of Bach in its own tempo. Sofia Gubaidulina (*Offertorium*) removes one note from each end of a theme of Bach in each variation, and builds it again from the end. These are methods to make new counterpoint from the lines of Bach.
12. Caroline Shaw (*Punctum*) fills a piece with the harmony of the Passion chorale but shows the chorale itself only late. Max Richter keeps 25 percent of the material of Vivaldi and puts it in loops. Thus the old music is a presence, not a quotation from start to end.
13. In works with a different harmony (Berg, Penderecki), a plain triad or a chorale is a strong event. The new work is primarily tonal: in it, the strong event can be the opposite: a moment that leaves the baroque language.

## Part 1: Measured tables

The study code made all tables of this part from the open data. The directory [`research/measured`](../research/measured) has the data files.

### M1. The style of the four-part chorales

The table compares all 370 chorale settings of the edition with the 11 settings of the St Matthew Passion. A share is a part of the moves of a voice, of the note time, or of the sounding time.

| Measure | All 370: middle value | All 370: middle 80 percent | Passion (11): middle value | Passion (11): lowest to highest |
| --- | --- | --- | --- | --- |
| Length (quarter notes) | 48 | 36 to 72 | 48 | 44 to 64 |
| Phrases (fermatas of the soprano) | 6 | 4 to 8 | 6 | 4 to 8 |
| Soprano: span (semitones) | 1200 % | 900 % to 1500 % | 1200 % | 900 % to 1300 % |
| Soprano: steps (semitone or whole tone) | 71 % | 59 % to 83 % | 74 % | 67 % to 80 % |
| Soprano: repeated notes | 13 % | 6 % to 26 % | 10 % | 4 % to 22 % |
| Bass: span (semitones) | 1750 % | 1400 % to 2200 % | 1900 % | 1300 % to 2100 % |
| Bass: semitone moves | 26 % | 19 % to 34 % | 31 % | 16 % to 40 % |
| Bass: steps (semitone or whole tone) | 64 % | 53 % to 73 % | 66 % | 57 % to 80 % |
| Bass: fourths and fifths | 21 % | 13 % to 30 % | 22 % | 11 % to 27 % |
| Bass: octaves and larger | 4 % | 0 % to 8 % | 4 % | 0 % to 9 % |
| Notes outside the scale (share of note time) | 3 % | 1 % to 6 % | 4 % | 3 % to 6 % |
| Note starts off the beat for each quarter note | 0.9 | 0.4 to 1.4 | 0.7 | 0.6 to 1.1 |
| Inner voices: mean note length (quarter notes) | 0.9 | 0.8 to 1.1 | 0.9 | 0.8 to 0.9 |
| Chords: share built from thirds | 88 % | 82 % to 94 % | 88 % | 84 % to 95 % |
| Chords: share with a semitone clash | 7 % | 3 % to 10 % | 7 % | 3 % to 16 % |
| Share of sounding time: major and minor triads | 61 % | 51 % to 70 % | 57 % | 50 % to 62 % |
| Share of sounding time: dominant chords | 9 % | 5 % to 14 % | 10 % | 3 % to 17 % |
| Share of sounding time: vagrant chords | 7 % | 3 % to 13 % | 7 % | 5 % to 16 % |
| Share of sounding time: other seventh and ninth chords | 8 % | 5 % to 12 % | 10 % | 5 % to 18 % |
| Mean distinct pitch classes in four quarter notes | 7 | 6.4 to 7.6 | 7 | 6.6 to 8 |

Data file: [`research/measured/chorale_style.csv`](../research/measured/chorale_style.csv)

### M2. The chorale settings of the St Matthew Passion

The edition of the chorales has 11 settings from the Passion (the settings of movements 15 and 17 are one setting in two keys). The edition gives some settings in a key that is not the key of the Passion: table S2 gives the keys of the Passion.

The column "Chords at the fermatas" gives the chord at the end of each phrase as a degree of the key: small letters are minor chords. The last setting (movement 62) ends on the dominant.

| Movement | Tune | Key of the edition | Quarter notes | Soprano | Bass | Chords at the fermatas | Notes outside the scale | Chords with a semitone clash | Bass semitone moves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | Herzliebster Jesu | B minor | 44 | F#4 to G5 | F#2 to D4 | V bIII V I | 3 % | 12 % | 27 % |
| 10 | O Welt, ich muss dich lassen | A-flat major | 48 | E-flat4 to E-flat5 | A-flat2 to C#4 | I V V VI III I | 3 % | 15 % | 34 % |
| 15 and 17 | Herzlich tut mich verlangen | D major | 48 | E4 to E5 | D2 to B3 | I vi I VI V I | 4 % | 6 % | 21 % |
| 25 | Was mein Gott will, das g'scheh allzeit | B minor | 48 | F#4 to E5 | A-flat2 to B3 | bIII i bVII V bIII I | 3 % | 7 % | 34 % |
| 32 | In dich hab ich gehoffet, Herr | B-flat major | 44 | B-flat4 to G5 | A2 to B-flat3 | I V V ii IV I | 6 % | 7 % | 40 % |
| 37 | O Welt, ich muss dich lassen | F major | 48 | C4 to C5 | F2 to D4 | I V V VI V I | 3 % | 9 % | 25 % |
| 40 | Werde munter, mein Gemüte | A major | 64 | A4 to G5 | E2 to B3 | V I V I ii IV V I | 3 % | 16 % | 16 % |
| 44 | Herzlich tut mich verlangen | D major | 48 | E4 to E5 | F#2 to B3 | I vi I VI V I | 6 % | 7 % | 31 % |
| 46 | Herzliebster Jesu | B minor | 44 | F#4 to G5 | B2 to D4 | V bIII i I | 4 % | 6 % | 35 % |
| 54 | Herzlich tut mich verlangen | F major | 48 | G4 to G5 | G2 to D4 | I vi I VI V I | 5 % | 7 % | 20 % |
| 62 | Herzlich tut mich verlangen | B minor | 48 | E4 to E5 | F#2 to C#4 | bIII i bIII I bVII V | 5 % | 3 % | 38 % |

Data file: [`research/measured/passion_chorales.csv`](../research/measured/passion_chorales.csv)

### M3. The chorale tunes of the Passion

The table gives the soprano of one setting of each tune, phrase by phrase, in the music language of the project (a `'` is one octave up; `is` is a sharp, `es` is a flat). The last column gives each note as semitones above the key note.

| Tune | Movement | Key of the edition | Phrase | Notes |
| --- | --- | --- | --- | --- |
| Herzliebster Jesu | 3 | B minor | 1 | `b'4 b'4 b'4 ais'8 gis'8 fis'4 b'4 cis''4 d''4 d''4 e''4 d''4 cis''4\fermata` |
| Herzliebster Jesu | 3 | B minor | 2 | `cis''4 d''4 e''4 fis''8 e''8 d''4 g''4 g''4 fis''8 e''8 fis''4 e''2 d''4\fermata` |
| Herzliebster Jesu | 3 | B minor | 3 | `d''4 cis''4 b'4 a'4 fis'8 g'8 a'4 a'4 b'4 a'4 g'2 fis'4\fermata` |
| Herzliebster Jesu | 3 | B minor | 4 | `fis''4 e''4 d''4 cis''2 b'2.\fermata` |
| O Welt, ich muss dich lassen | 10 | A-flat major | 1 | `c''4 as'4 bes'4 c''8 des''8 es''4 des''2 c''4\fermata` |
| O Welt, ich muss dich lassen | 10 | A-flat major | 2 | `c''8 des''8 es''4 es''4 bes'4 c''4 as'2 g'4\fermata` |
| O Welt, ich muss dich lassen | 10 | A-flat major | 3 | `es'4 as'4 bes'4 c''4 c''4 bes'2.\fermata` |
| O Welt, ich muss dich lassen | 10 | A-flat major | 4 | `c''4 as'4 bes'4 c''8 des''8 es''4 des''2 c''4\fermata` |
| O Welt, ich muss dich lassen | 10 | A-flat major | 5 | `c''8 des''8 es''4 es''4 bes'4 c''4 as'2 g'4\fermata` |
| O Welt, ich muss dich lassen | 10 | A-flat major | 6 | `es'4 as'4 bes'4 c''4 des''4 c''4 bes'4 as'4\fermata` |
| Herzlich tut mich verlangen | 15 and 17 | D major | 1 | `fis'4 b'4 a'4 g'4 fis'4 e'2 fis'4\fermata` |
| Herzlich tut mich verlangen | 15 and 17 | D major | 2 | `cis''4 d''4 d''4 cis''8 b'8 cis''4 b'2.\fermata` |
| Herzlich tut mich verlangen | 15 and 17 | D major | 3 | `d''4 cis''8 b'8 a'4 b'4 cis''4 d''2 d''4\fermata` |
| Herzlich tut mich verlangen | 15 and 17 | D major | 4 | `a'4 b'4 a'4 g'4 g'4 fis'2.\fermata` |
| Herzlich tut mich verlangen | 15 and 17 | D major | 5 | `d''4 cis''8 d''8 e''4 d''4 cis''4 b'2 cis''4\fermata` |
| Herzlich tut mich verlangen | 15 and 17 | D major | 6 | `fis'4 g'4 fis'4 e'4 a'4 fis'2.\fermata` |
| Was mein Gott will, das g'scheh allzeit | 25 | B minor | 1 | `fis'8 g'8 a'4 b'4 a'4 d''4 d''4 cis''4 d''4\fermata` |
| Was mein Gott will, das g'scheh allzeit | 25 | B minor | 2 | `d''4 cis''4 b'4 e''4 d''8 cis''8 cis''2 b'4\fermata` |
| Was mein Gott will, das g'scheh allzeit | 25 | B minor | 3 | `b'4 b'4 b'4 cis''8 b'8 a'4 a'4 gis'4 a'4\fermata` |
| Was mein Gott will, das g'scheh allzeit | 25 | B minor | 4 | `a'4 b'4 cis''4 d''4 cis''4 b'2 cis''4\fermata` |
| Was mein Gott will, das g'scheh allzeit | 25 | B minor | 5 | `fis'8 g'8 a'4 b'4 a'4 d''4 d''4 cis''4 d''4\fermata` |
| Was mein Gott will, das g'scheh allzeit | 25 | B minor | 6 | `d''4 cis''4 b'4 e''4 d''8 cis''8 cis''2 b'4\fermata` |
| In dich hab ich gehoffet, Herr | 32 | B-flat major | 1 | `bes'4 bes'4 f''4 f''4 es''8 d''8 c''4 d''4 es''8 d''8 c''4 bes'4\fermata` |
| In dich hab ich gehoffet, Herr | 32 | B-flat major | 2 | `bes'4 c''4 d''4 es''4 c''4 f''4 g''4 f''4\fermata` |
| In dich hab ich gehoffet, Herr | 32 | B-flat major | 3 | `d''4 d''8 es''8 f''4 es''4 d''8 c''8 bes'8 c''8 d''8 c''8 c''4\fermata` |
| In dich hab ich gehoffet, Herr | 32 | B-flat major | 4 | `d''4 bes'8 c''8 d''4 es''4\fermata` |
| In dich hab ich gehoffet, Herr | 32 | B-flat major | 5 | `d''4 c''4 d''4 es''4\fermata` |
| In dich hab ich gehoffet, Herr | 32 | B-flat major | 6 | `d''4 c''4 bes'4 f''4. es''8 d''4 es''8 d''8 c''2 bes'4\fermata` |
| Werde munter, mein Gemüte | 40 | A major | 1 | `cis''4 d''4 e''4 e''4 d''4 cis''4 b'4 b'4\fermata` |
| Werde munter, mein Gemüte | 40 | A major | 2 | `cis''4 d''4 e''4 d''8 cis''8 b'4. a'8 a'2\fermata` |
| Werde munter, mein Gemüte | 40 | A major | 3 | `cis''4 d''4 e''4 e''4 d''4 cis''4 b'4 b'4\fermata` |
| Werde munter, mein Gemüte | 40 | A major | 4 | `cis''4 d''4 e''4 d''8 cis''8 b'4. a'8 a'2\fermata` |
| Werde munter, mein Gemüte | 40 | A major | 5 | `b'4 cis''4 d''8 cis''8 d''8 e''8 cis''4 cis''4 b'2\fermata` |
| Werde munter, mein Gemüte | 40 | A major | 6 | `d''4 e''4 fis''4 e''8 fis''16 g''16 fis''4 e''8 d''8 d''2\fermata` |
| Werde munter, mein Gemüte | 40 | A major | 7 | `cis''4 d''4 e''4 e''4 d''4 cis''4 b'4 b'4\fermata` |
| Werde munter, mein Gemüte | 40 | A major | 8 | `cis''4 d''4 e''4 a'8 b'8 cis''4 b'8 a'8 a'4 a'4\fermata` |

Data file: [`research/measured/chorale_tunes.csv`](../research/measured/chorale_tunes.csv)

### M4. The voice lines

Each row is one solo voice of one movement. "Middle" is the pitch below which the voice is for one half of its time. The voice is between the 5 % point and the 95 % point for 90 percent of its time. The columns from "Repeated" to "Sixths or larger" give the moves from note to note as shares of all moves.

| Movement | Line | Notes | Lowest | 5 % point | Middle | 95 % point | Highest | Time with notes | Notes in a quarter note | Sixteenths or shorter | Repeated | Semitone | Whole tone | Thirds | Fourths, fifths | Sixths or larger | Outside the scale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 39. Erbarme dich (aria, alto) | voice: alto | 305 | B3 | E-flat4 | A4 | D5 | E5 | 60 % | 0.94 | 34 % | 7 % | 34 % | 37 % | 14 % | 5 % | 2 % | 10 % |
| 52. Können Tränen meiner Wangen (aria, alto) | voice: alto | 333 | C4 | D4 | A4 | D5 | E-flat5 | 50 % | 1.23 | 60 % | 6 % | 37 % | 37 % | 10 % | 5 % | 5 % | 10 % |
| 49. Aus Liebe will mein Heiland sterben (aria, soprano) | voice: soprano | 184 | E4 | G4 | D5 | F5 | G5 | 51 % | 0.83 | 33 % | 18 % | 28 % | 27 % | 14 % | 7 % | 5 % | 9 % |
| 8. Blute nur, du liebes Herz (aria, soprano) | voice: soprano | 228 | E4 | E4 | C#5 | F#5 | G5 | 46 % | 0.78 | 21 % | 6 % | 36 % | 26 % | 18 % | 8 % | 6 % | 11 % |
| 65. Mache dich, mein Herze, rein (aria, bass) | voice: bass | 376 | A2 | B-flat2 | G3 | D4 | E-flat4 | 54 % | 0.78 | 4 % | 3 % | 32 % | 29 % | 16 % | 10 % | 11 % | 7 % |
| Et misericordia (duet, alto and tenor) | voice: alto | 173 | A3 | C#4 | F#4 | B4 | C#5 | 55 % | 0.82 | 0 % | 9 % | 38 % | 37 % | 5 % | 6 % | 6 % | 12 % |
| Et misericordia (duet, alto and tenor) | voice: tenor | 176 | E3 | F#3 | C4 | F4 | G4 | 55 % | 0.84 | 0 % | 11 % | 35 % | 38 % | 7 % | 5 % | 4 % | 8 % |
| 13. Ach, mein Sinn (aria, tenor) | voice: tenor | 264 | E3 | F#3 | C#4 | A-flat4 | A4 | 67 % | 0.97 | 37 % | 10 % | 27 % | 28 % | 22 % | 10 % | 4 % | 6 % |
| 8. Der Ewigkeit saphirnes Haus (aria, tenor) | voice: tenor | 385 | D3 | F#3 | C4 | G4 | A4 | 53 % | 1.35 | 70 % | 3 % | 28 % | 41 % | 17 % | 8 % | 4 % | 2 % |

Data file: [`research/measured/lines.csv`](../research/measured/lines.csv)

### M5. The lines of the instruments

Each row is one instrument line of one movement. A line with more than one note at a time counts with its highest note.

| Movement | Line | Notes | Lowest | 5 % point | Middle | 95 % point | Highest | Time with notes | Notes in a quarter note | Sixteenths or shorter | Repeated | Semitone | Whole tone | Thirds | Fourths, fifths | Sixths or larger | Outside the scale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 39. Erbarme dich (aria, alto) | solo: violin | 712 | B3 | F#4 | D5 | B5 | E6 | 83 % | 2.20 | 62 % | 4 % | 32 % | 41 % | 12 % | 8 % | 4 % | 8 % |
| 39. Erbarme dich (aria, alto) | strings: violin 1 | 253 | D4 | G4 | D5 | G5 | B5 | 93 % | 0.78 | 10 % | 7 % | 32 % | 34 % | 11 % | 12 % | 4 % | 7 % |
| 39. Erbarme dich (aria, alto) | strings: violin 2 | 266 | B-flat3 | D4 | B4 | E5 | A5 | 93 % | 0.82 | 0 % | 12 % | 30 % | 29 % | 16 % | 8 % | 5 % | 7 % |
| 39. Erbarme dich (aria, alto) | strings: viola | 280 | D3 | G3 | E4 | B-flat4 | C#5 | 93 % | 0.87 | 0 % | 20 % | 19 % | 25 % | 9 % | 17 % | 10 % | 4 % |
| 39. Erbarme dich (aria, alto) | continuo | 535 | C#2 | E2 | D3 | C#4 | E4 | 87 % | 1.66 | 0 % | 59 % | 8 % | 9 % | 12 % | 9 % | 3 % | 2 % |
| 52. Können Tränen meiner Wangen (aria, alto) | strings: violins | 452 | G3 | B-flat3 | G4 | F5 | C6 | 77 % | 1.67 | 53 % | 6 % | 19 % | 22 % | 21 % | 17 % | 15 % | 4 % |
| 52. Können Tränen meiner Wangen (aria, alto) | continuo | 402 | C2 | E-flat2 | D3 | B-flat3 | E4 | 75 % | 1.48 | 33 % | 0 % | 7 % | 14 % | 32 % | 25 % | 22 % | 4 % |
| 49. Aus Liebe will mein Heiland sterben (aria, soprano) | solo: flute | 552 | E4 | B4 | F5 | C6 | E-flat6 | 87 % | 2.50 | 85 % | 6 % | 33 % | 35 % | 18 % | 5 % | 4 % | 8 % |
| 49. Aus Liebe will mein Heiland sterben (aria, soprano) | winds: oboe da caccia 1 | 253 | A3 | D4 | A4 | D5 | E5 | 93 % | 1.14 | 19 % | 39 % | 24 % | 20 % | 12 % | 4 % | 1 % | 4 % |
| 49. Aus Liebe will mein Heiland sterben (aria, soprano) | winds: oboe da caccia 2 | 256 | F3 | A3 | E4 | A4 | C5 | 94 % | 1.16 | 19 % | 42 % | 24 % | 21 % | 5 % | 6 % | 3 % | 13 % |
| 8. Blute nur, du liebes Herz (aria, soprano) | winds: flute 1 | 508 | D4 | F4 | E-flat5 | B-flat5 | C#6 | 98 % | 1.73 | 10 % | 15 % | 26 % | 23 % | 10 % | 8 % | 18 % | 8 % |
| 8. Blute nur, du liebes Herz (aria, soprano) | winds: flute 2 | 324 | D4 | E4 | D5 | A5 | B5 | 63 % | 1.11 | 0 % | 22 % | 18 % | 22 % | 6 % | 8 % | 24 % | 5 % |
| 8. Blute nur, du liebes Herz (aria, soprano) | strings: violin 1 | 378 | C#4 | F#4 | E5 | B5 | C#6 | 79 % | 1.29 | 0 % | 24 % | 20 % | 21 % | 3 % | 8 % | 23 % | 6 % |
| 8. Blute nur, du liebes Herz (aria, soprano) | strings: violin 2 | 378 | A3 | D4 | B4 | F#5 | A5 | 79 % | 1.29 | 0 % | 26 % | 15 % | 23 % | 6 % | 7 % | 23 % | 2 % |
| 8. Blute nur, du liebes Herz (aria, soprano) | strings: viola | 285 | E3 | F#3 | C#4 | G4 | B4 | 80 % | 0.97 | 0 % | 6 % | 19 % | 21 % | 22 % | 27 % | 6 % | 1 % |
| 8. Blute nur, du liebes Herz (aria, soprano) | continuo | 337 | D2 | F#2 | D3 | C#4 | G4 | 70 % | 1.15 | 0 % | 11 % | 24 % | 24 % | 11 % | 17 % | 13 % | 6 % |
| 65. Mache dich, mein Herze, rein (aria, bass) | strings: violin 1 | 1041 | G3 | B-flat3 | G4 | E-flat5 | A-flat5 | 89 % | 2.16 | 69 % | 26 % | 19 % | 29 % | 8 % | 10 % | 8 % | 6 % |
| 65. Mache dich, mein Herze, rein (aria, bass) | strings: violin 2 | 565 | A3 | B-flat3 | E-flat4 | C5 | F5 | 87 % | 1.17 | 9 % | 9 % | 25 % | 28 % | 21 % | 10 % | 7 % | 3 % |
| 65. Mache dich, mein Herze, rein (aria, bass) | strings: viola | 476 | D3 | F3 | B-flat3 | G4 | C5 | 87 % | 0.99 | 0 % | 7 % | 16 % | 28 % | 23 % | 16 % | 9 % | 3 % |
| 65. Mache dich, mein Herze, rein (aria, bass) | continuo | 677 | C2 | E-flat2 | C3 | B-flat3 | C4 | 98 % | 1.41 | 0 % | 14 % | 11 % | 26 % | 10 % | 6 % | 33 % | 6 % |
| 29. O Mensch, bewein dein Sünde groß (chorale fantasia) | winds: flute 1 | 956 | E4 | A-flat4 | E5 | C#6 | E6 | 87 % | 2.43 | 89 % | 47 % | 15 % | 17 % | 6 % | 7 % | 9 % | 16 % |
| 29. O Mensch, bewein dein Sünde groß (chorale fantasia) | winds: flute 2 | 712 | C#4 | E-flat4 | C#5 | A5 | C#6 | 80 % | 1.81 | 64 % | 38 % | 17 % | 21 % | 12 % | 8 % | 4 % | 14 % |
| 29. O Mensch, bewein dein Sünde groß (chorale fantasia) | strings: violin 1 | 616 | A3 | E-flat4 | C#5 | A5 | C#6 | 76 % | 1.57 | 55 % | 35 % | 22 % | 29 % | 5 % | 6 % | 3 % | 15 % |
| 29. O Mensch, bewein dein Sünde groß (chorale fantasia) | strings: violin 2 | 606 | A3 | C#4 | A4 | F5 | B-flat5 | 77 % | 1.54 | 48 % | 33 % | 19 % | 28 % | 9 % | 7 % | 3 % | 7 % |
| 29. O Mensch, bewein dein Sünde groß (chorale fantasia) | strings: viola | 612 | E3 | A-flat3 | F#4 | C#5 | E5 | 76 % | 1.56 | 44 % | 32 % | 15 % | 26 % | 13 % | 9 % | 5 % | 10 % |
| 29. O Mensch, bewein dein Sünde groß (chorale fantasia) | continuo | 641 | C#2 | E2 | B2 | A3 | C#4 | 88 % | 1.63 | 77 % | 44 % | 14 % | 22 % | 5 % | 7 % | 8 % | 9 % |
| 68. Wir setzen uns mit Tränen nieder (chorus) | strings: violin 1 | 511 | D4 | E-flat4 | B4 | G5 | A-flat5 | 91 % | 1.33 | 13 % | 12 % | 30 % | 35 % | 13 % | 6 % | 5 % | 6 % |
| 68. Wir setzen uns mit Tränen nieder (chorus) | strings: violin 2 | 471 | C4 | D4 | F4 | C5 | F5 | 91 % | 1.23 | 8 % | 17 % | 33 % | 32 % | 9 % | 7 % | 1 % | 4 % |
| 68. Wir setzen uns mit Tränen nieder (chorus) | strings: viola | 363 | E-flat3 | G3 | C4 | G4 | B-flat4 | 91 % | 0.95 | 0 % | 19 % | 16 % | 26 % | 17 % | 13 % | 8 % | 4 % |
| 68. Wir setzen uns mit Tränen nieder (chorus) | continuo | 508 | C2 | C2 | A-flat2 | B-flat3 | E-flat4 | 91 % | 1.32 | 0 % | 21 % | 11 % | 16 % | 28 % | 12 % | 12 % | 4 % |
| Crucifixus (chorus on a ground bass) | winds: flute 1 | 108 | E-flat4 | F#4 | E5 | B5 | C6 | 68 % | 0.34 | 0 % | 0 % | 15 % | 7 % | 30 % | 28 % | 20 % | 9 % |
| Crucifixus (chorus on a ground bass) | winds: flute 2 | 108 | D4 | E-flat4 | A4 | A-flat5 | B5 | 68 % | 0.34 | 0 % | 8 % | 7 % | 15 % | 27 % | 21 % | 21 % | 8 % |
| Crucifixus (chorus on a ground bass) | strings: violin 1 | 100 | B3 | E-flat4 | B4 | G5 | B5 | 62 % | 0.31 | 0 % | 21 % | 27 % | 27 % | 6 % | 15 % | 4 % | 5 % |
| Crucifixus (chorus on a ground bass) | strings: violin 2 | 100 | G3 | A3 | G4 | C5 | E-flat5 | 62 % | 0.31 | 0 % | 21 % | 23 % | 29 % | 13 % | 12 % | 2 % | 8 % |
| Crucifixus (chorus on a ground bass) | strings: viola | 100 | E-flat3 | E3 | E-flat4 | A4 | B4 | 62 % | 0.31 | 0 % | 23 % | 15 % | 25 % | 8 % | 25 % | 4 % | 11 % |
| Crucifixus (chorus on a ground bass) | continuo | 313 | D2 | E2 | C#3 | E3 | E3 | 100 % | 0.98 | 0 % | 70 % | 21 % | 1 % | 0 % | 4 % | 4 % | 0 % |
| Qui tollis peccata mundi (chorus) | winds: flute 1 | 282 | F#4 | C5 | F#5 | D6 | E6 | 82 % | 1.87 | 90 % | 20 % | 23 % | 34 % | 17 % | 2 % | 4 % | 9 % |
| Qui tollis peccata mundi (chorus) | winds: flute 2 | 286 | E4 | G4 | C#5 | G5 | B5 | 83 % | 1.89 | 91 % | 19 % | 21 % | 37 % | 15 % | 3 % | 5 % | 9 % |
| Qui tollis peccata mundi (chorus) | strings: violin 1 | 156 | C#4 | F4 | B4 | E5 | G5 | 99 % | 1.03 | 13 % | 2 % | 25 % | 40 % | 14 % | 11 % | 7 % | 9 % |
| Qui tollis peccata mundi (chorus) | strings: violin 2 | 158 | A-flat3 | C#4 | F#4 | E5 | F#5 | 99 % | 1.05 | 6 % | 4 % | 18 % | 33 % | 17 % | 21 % | 7 % | 5 % |
| Qui tollis peccata mundi (chorus) | strings: viola | 230 | C#3 | F3 | C#4 | A-flat4 | B-flat4 | 100 % | 1.52 | 5 % | 3 % | 14 % | 11 % | 29 % | 27 % | 16 % | 13 % |
| Qui tollis peccata mundi (chorus) | strings: violoncello | 148 | C2 | C#2 | G2 | E3 | B3 | 99 % | 0.98 | 0 % | 59 % | 7 % | 5 % | 9 % | 17 % | 3 % | 13 % |
| Qui tollis peccata mundi (chorus) | continuo | 70 | C2 | C#2 | A-flat2 | A-flat3 | B3 | 48 % | 0.46 | 0 % | 3 % | 17 % | 10 % | 17 % | 37 % | 17 % | 12 % |
| Et misericordia (duet, alto and tenor) | strings: violin 1 | 234 | D4 | E4 | B4 | G5 | B-flat5 | 73 % | 1.11 | 0 % | 12 % | 32 % | 38 % | 5 % | 6 % | 6 % | 11 % |
| Et misericordia (duet, alto and tenor) | strings: violin 2 | 223 | A3 | E-flat4 | G4 | E5 | F#5 | 72 % | 1.06 | 0 % | 13 % | 31 % | 38 % | 10 % | 7 % | 1 % | 13 % |
| Et misericordia (duet, alto and tenor) | strings: viola | 181 | E3 | G3 | E4 | A4 | C#5 | 72 % | 0.86 | 0 % | 12 % | 24 % | 32 % | 11 % | 16 % | 5 % | 9 % |
| Et misericordia (duet, alto and tenor) | continuo | 283 | C2 | D2 | C3 | B3 | D4 | 100 % | 1.35 | 0 % | 29 % | 11 % | 6 % | 3 % | 5 % | 45 % | 4 % |
| 13. Ach, mein Sinn (aria, tenor) | strings: violin 1 | 489 | E-flat4 | F#4 | C#5 | A-flat5 | D6 | 94 % | 1.80 | 60 % | 21 % | 26 % | 30 % | 13 % | 5 % | 5 % | 7 % |
| 13. Ach, mein Sinn (aria, tenor) | strings: violin 2 | 258 | B3 | D4 | A-flat4 | C#5 | F#5 | 90 % | 0.95 | 27 % | 10 % | 36 % | 29 % | 12 % | 11 % | 2 % | 5 % |
| 13. Ach, mein Sinn (aria, tenor) | strings: viola | 235 | F#3 | A3 | E4 | A-flat4 | C#5 | 90 % | 0.86 | 23 % | 9 % | 22 % | 39 % | 11 % | 16 % | 4 % | 3 % |
| 13. Ach, mein Sinn (aria, tenor) | continuo | 278 | C#2 | F2 | D3 | C#4 | E4 | 96 % | 1.02 | 27 % | 6 % | 31 % | 32 % | 13 % | 8 % | 11 % | 9 % |
| 1. Herr, unser Herrscher (chorus) | winds: flute 1 | 351 | C4 | G4 | E5 | B-flat5 | C6 | 94 % | 0.58 | 11 % | 0 % | 38 % | 35 % | 11 % | 8 % | 7 % | 10 % |
| 1. Herr, unser Herrscher (chorus) | winds: flute 2 | 354 | D4 | G4 | D5 | A5 | A5 | 93 % | 0.58 | 11 % | 0 % | 38 % | 36 % | 9 % | 11 % | 5 % | 8 % |
| 1. Herr, unser Herrscher (chorus) | strings: violin 1 | 2099 | B-flat3 | D4 | B-flat4 | F5 | E-flat6 | 92 % | 3.45 | 94 % | 1 % | 36 % | 52 % | 9 % | 2 % | 1 % | 7 % |
| 1. Herr, unser Herrscher (chorus) | strings: violin 2 | 2085 | G3 | B-flat3 | G4 | D5 | C6 | 92 % | 3.42 | 94 % | 0 % | 37 % | 49 % | 9 % | 3 % | 2 % | 6 % |
| 1. Herr, unser Herrscher (chorus) | strings: viola | 1610 | C#3 | G3 | D4 | A4 | E5 | 92 % | 2.64 | 65 % | 3 % | 23 % | 38 % | 12 % | 17 % | 7 % | 6 % |
| 1. Herr, unser Herrscher (chorus) | continuo | 1365 | C2 | D2 | G2 | D3 | F3 | 99 % | 2.24 | 23 % | 71 % | 12 % | 12 % | 1 % | 4 % | 0 % | 4 % |
| 1. Lass, Fürstin, lass noch einen Strahl (chorus) | winds: flute 1 | 684 | E-flat4 | F#4 | E5 | D6 | F#6 | 84 % | 2.48 | 47 % | 14 % | 31 % | 24 % | 14 % | 9 % | 8 % | 11 % |
| 1. Lass, Fürstin, lass noch einen Strahl (chorus) | winds: flute 2 | 609 | D4 | E4 | B4 | A5 | D6 | 83 % | 2.21 | 46 % | 12 % | 28 % | 25 % | 17 % | 9 % | 9 % | 9 % |
| 1. Lass, Fürstin, lass noch einen Strahl (chorus) | winds: oboe d'amore 1 | 632 | B3 | E-flat4 | D5 | A5 | B5 | 80 % | 2.29 | 43 % | 19 % | 32 % | 25 % | 9 % | 8 % | 6 % | 14 % |
| 1. Lass, Fürstin, lass noch einen Strahl (chorus) | winds: oboe d'amore 2 | 570 | B-flat3 | C#4 | A4 | F#5 | B5 | 80 % | 2.07 | 41 % | 15 % | 30 % | 26 % | 13 % | 9 % | 8 % | 11 % |
| 1. Lass, Fürstin, lass noch einen Strahl (chorus) | strings: violin 1 | 651 | A-flat3 | C#4 | B4 | B-flat5 | D6 | 86 % | 2.36 | 36 % | 36 % | 22 % | 18 % | 10 % | 9 % | 6 % | 9 % |
| 1. Lass, Fürstin, lass noch einen Strahl (chorus) | strings: violin 2 | 590 | G3 | C#4 | G4 | F#5 | B5 | 86 % | 2.14 | 33 % | 34 % | 16 % | 19 % | 12 % | 12 % | 6 % | 5 % |
| 1. Lass, Fürstin, lass noch einen Strahl (chorus) | strings: viola | 543 | C#3 | G3 | E4 | B4 | E5 | 86 % | 1.97 | 28 % | 38 % | 17 % | 10 % | 13 % | 15 % | 6 % | 7 % |
| 1. Lass, Fürstin, lass noch einen Strahl (chorus) | strings: viola da gamba 1 | 698 | C#3 | F#3 | E-flat4 | B4 | D5 | 79 % | 2.53 | 50 % | 12 % | 27 % | 27 % | 18 % | 9 % | 6 % | 10 % |
| 1. Lass, Fürstin, lass noch einen Strahl (chorus) | strings: viola da gamba 2 | 669 | A-flat2 | E3 | B3 | G4 | B4 | 79 % | 2.42 | 49 % | 12 % | 23 % | 28 % | 19 % | 11 % | 7 % | 6 % |
| 1. Lass, Fürstin, lass noch einen Strahl (chorus) | continuo | 447 | C#2 | D2 | C#3 | B3 | E4 | 82 % | 1.62 | 0 % | 0 % | 5 % | 5 % | 3 % | 6 % | 81 % | 11 % |
| 8. Der Ewigkeit saphirnes Haus (aria, tenor) | solo: flute | 529 | D4 | A4 | E5 | B5 | E6 | 78 % | 1.86 | 66 % | 5 % | 31 % | 42 % | 9 % | 8 % | 5 % | 3 % |
| 8. Der Ewigkeit saphirnes Haus (aria, tenor) | solo: oboe d'amore | 291 | B3 | E4 | B4 | G5 | B5 | 68 % | 1.02 | 10 % | 8 % | 28 % | 27 % | 23 % | 8 % | 7 % | 6 % |
| 8. Der Ewigkeit saphirnes Haus (aria, tenor) | strings: violin 1 | 212 | B3 | D4 | B4 | F#5 | G5 | 70 % | 0.74 | 0 % | 13 % | 24 % | 20 % | 29 % | 12 % | 3 % | 4 % |
| 8. Der Ewigkeit saphirnes Haus (aria, tenor) | strings: violin 2 | 212 | A3 | B3 | F#4 | B4 | E5 | 70 % | 0.74 | 0 % | 19 % | 13 % | 31 % | 16 % | 22 % | 0 % | 3 % |
| 8. Der Ewigkeit saphirnes Haus (aria, tenor) | strings: violas da gamba | 660 | D2 | F#2 | G3 | F#4 | A4 | 97 % | 2.32 | 40 % | 21 % | 21 % | 27 % | 3 % | 3 % | 25 % | 3 % |
| 8. Der Ewigkeit saphirnes Haus (aria, tenor) | continuo | 215 | C2 | E-flat2 | B2 | G3 | C4 | 70 % | 0.75 | 0 % | 2 % | 17 % | 23 % | 12 % | 38 % | 8 % | 3 % |

Data file: [`research/measured/lines.csv`](../research/measured/lines.csv)

### M6. The harmony and the texture of the movements

The tempo and the duration are those of the MIDI file of the edition: they are a decision of the editor, not of Bach. "Vagrant chords" are diminished and augmented chords and other chords that do not belong to one key. A "semitone clash" is a chord that has two notes one semitone apart: passing notes and suspensions make most of them.

| Movement | Key | Metre | Bars | Seconds | Lines | Mean lines that sound | Pitch classes in one bar | Chords from thirds | Chords with a semitone clash | Major and minor triads | Dominant chords | Vagrant chords | Notes outside the scale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 39. Erbarme dich (aria, alto) | B minor | 12/8 | 54 | 373 | 6 | 5.1 | 8.0 | 71 % | 28 % | 27 % | 15 % | 11 % | 6 % |
| 52. Können Tränen meiner Wangen (aria, alto) | G minor | 3/4 | 90 | 246 | 3 | 2.0 | 5.6 | 67 % | 20 % | 4 % | 2 % | 2 % | 5 % |
| 49. Aus Liebe will mein Heiland sterben (aria, soprano) | A minor | 3/4 | 74 | 255 | 4 | 3.3 | 7.2 | 76 % | 15 % | 25 % | 10 % | 15 % | 9 % |
| 8. Blute nur, du liebes Herz (aria, soprano) | B minor | 4/4 | 73 | 275 | 7 | 5.2 | 7.3 | 77 % | 13 % | 30 % | 4 % | 18 % | 5 % |
| 65. Mache dich, mein Herze, rein (aria, bass) | B-flat major | 12/8 | 80 | 385 | 5 | 4.1 | 7.3 | 73 % | 17 % | 35 % | 9 % | 4 % | 5 % |
| 29. O Mensch, bewein dein Sünde groß (chorale fantasia) | E major | 4/4 | 98 | 393 | 10 | 6.6 | 7.9 | 65 % | 42 % | 26 % | 17 % | 7 % | 12 % |
| 68. Wir setzen uns mit Tränen nieder (chorus) | C minor | 3/4 | 128 | 349 | 16 | 10.5 | 6.6 | 82 % | 18 % | 41 % | 17 % | 14 % | 5 % |
| Crucifixus (chorus on a ground bass) | E minor | 3/2 | 53 | 140 | 10 | 6.9 | 6.2 | 89 % | 15 % | 41 % | 16 % | 25 % | 8 % |
| Qui tollis peccata mundi (chorus) | B minor | 3/4 | 50 | 162 | 11 | 9.4 | 7.7 | 61 % | 49 % | 21 % | 14 % | 11 % | 10 % |
| Et misericordia (duet, alto and tenor) | E minor | 12/8 | 35 | 175 | 6 | 4.3 | 7.8 | 79 % | 23 % | 29 % | 16 % | 16 % | 9 % |
| 13. Ach, mein Sinn (aria, tenor) | F# minor | 3/4 | 91 | 170 | 5 | 4.4 | 6.7 | 78 % | 18 % | 21 % | 28 % | 14 % | 6 % |
| 1. Herr, unser Herrscher (chorus) | G minor | 4/4 | 152 | 609 | 10 | 8.1 | 8.4 | 49 % | 58 % | 12 % | 14 % | 12 % | 7 % |
| 1. Lass, Fürstin, lass noch einen Strahl (chorus) | B minor | 4/4 | 69 | 394 | 14 | 10.4 | 9.0 | 74 % | 30 % | 29 % | 17 % | 16 % | 9 % |
| 8. Der Ewigkeit saphirnes Haus (aria, tenor) | E minor | 3/4 | 95 | 295 | 7 | 5.1 | 7.0 | 71 % | 26 % | 30 % | 10 % | 9 % | 3 % |

Data file: [`research/measured/movement_harmony.csv`](../research/measured/movement_harmony.csv)

### M7. The bass lines

Each row is the continuo line of one movement. "Longest pedal" is the longest time for which the bass stays on one note.

| Movement | Lowest | Highest | Notes in a quarter note | Sixteenths or shorter | Eighths | Repeated note | Semitone | Steps | Fourth or fifth | Sixth or larger | Longest pedal (quarter notes) | Pedal note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 39. Erbarme dich (aria, alto) | C#2 | E4 | 1.66 | 0 % | 96 % | 59 % | 8 % | 17 % | 9 % | 3 % | 7.5 | E3 |
| 52. Können Tränen meiner Wangen (aria, alto) | C2 | E4 | 1.48 | 33 % | 33 % | 0 % | 7 % | 21 % | 25 % | 22 % | 1.75 | E-flat3 |
| 8. Blute nur, du liebes Herz (aria, soprano) | D2 | G4 | 1.15 | 0 % | 78 % | 11 % | 24 % | 48 % | 17 % | 13 % | 2.5 | B2 |
| 65. Mache dich, mein Herze, rein (aria, bass) | C2 | C4 | 1.41 | 0 % | 62 % | 14 % | 11 % | 36 % | 6 % | 33 % | 2 | F2 |
| 29. O Mensch, bewein dein Sünde groß (chorale fantasia) | C#2 | C#4 | 1.63 | 77 % | 14 % | 44 % | 14 % | 36 % | 7 % | 8 % | 13.25 | E2 |
| 68. Wir setzen uns mit Tränen nieder (chorus) | C2 | E-flat4 | 1.32 | 0 % | 66 % | 21 % | 11 % | 27 % | 12 % | 12 % | 9 | C2 |
| Crucifixus (chorus on a ground bass) | D2 | E3 | 0.98 | 0 % | 0 % | 70 % | 21 % | 22 % | 4 % | 4 % | 6 | B2 |
| Qui tollis peccata mundi (chorus) | C2 | B3 | 0.46 | 0 % | 1 % | 3 % | 17 % | 27 % | 37 % | 17 % | 3 | F#2 |
| Et misericordia (duet, alto and tenor) | C2 | D4 | 1.35 | 0 % | 53 % | 29 % | 11 % | 17 % | 5 % | 45 % | 3 | B2 |
| 13. Ach, mein Sinn (aria, tenor) | C#2 | E4 | 1.02 | 27 % | 12 % | 6 % | 31 % | 63 % | 8 % | 11 % | 8 | C#3 |
| 1. Herr, unser Herrscher (chorus) | C2 | F3 | 2.24 | 23 % | 77 % | 71 % | 12 % | 24 % | 4 % | 0 % | 48 | G2 |
| 1. Lass, Fürstin, lass noch einen Strahl (chorus) | C#2 | E4 | 1.62 | 0 % | 100 % | 0 % | 5 % | 10 % | 6 % | 81 % | 4 | B2 |
| 8. Der Ewigkeit saphirnes Haus (aria, tenor) | C2 | C4 | 0.75 | 0 % | 18 % | 2 % | 17 % | 40 % | 38 % | 8 % | 3 | E2 |

Data file: [`research/measured/bass_lines.csv`](../research/measured/bass_lines.csv)

### M8. The figures of the figured bass

The table counts the figures in the text sources of the movements that have a figured bass. The numbers of a figure are from the top to the bottom. A `+` is a raised note, a `-` is a lowered note, a `!` is a natural sign; a figure with only a sign changes the third. The table shows the figures that come five times or more.

| Figure | Count | Share |
| --- | --- | --- |
| `6` | 169 | 19 % |
| `6 4` | 54 | 6 % |
| `6 5` | 53 | 6 % |
| `7 +` | 51 | 6 % |
| `5` | 50 | 5 % |
| `7` | 49 | 5 % |
| `+` | 48 | 5 % |
| `5 3` | 28 | 3 % |
| `6 4 2` | 28 | 3 % |
| `7 !` | 21 | 2 % |
| `4 2` | 20 | 2 % |
| `6\\` | 18 | 2 % |
| `7 4 2` | 18 | 2 % |
| `4` | 16 | 2 % |
| `6 4 3` | 16 | 2 % |
| `6!` | 16 | 2 % |
| `6/` | 16 | 2 % |
| `7 5` | 15 | 2 % |
| `8` | 15 | 2 % |
| `6 4\+ 2` | 9 | 1 % |
| `7!` | 8 | 1 % |
| `!` | 6 | 1 % |
| `-` | 6 | 1 % |
| `6/ 5!` | 6 | 1 % |
| `6\\ 5!` | 6 | 1 % |
| `3` | 5 | 1 % |
| `4 2+` | 5 | 1 % |
| `6 4\+ 2\+` | 5 | 1 % |
| `6-` | 5 | 1 % |
| `6/ 4\+ 2` | 5 | 1 % |
| `7! 5` | 5 | 1 % |
| `7-` | 5 | 1 % |
| `9` | 5 | 1 % |
| `(movements with figures)` | 6 |  |
| `(all figures)` | 910 |  |

Data file: [`research/measured/figures.csv`](../research/measured/figures.csv)

## Part 2: Sourced tables

The study team wrote the tables of this part from the sources. The directory [`research/tables`](../research/tables) has the data files.

### S1. The works of the study

The table lists the works that the study team examined: works of Bach, music for one voice of his time, and works of later composers that use the music of Bach or the form of the Passion. The column "Lesson for this work" gives what the new work takes from each.

| Composer | Work | Year | Forces | Minutes | Lesson for this work | Source | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| J. S. Bach | St Matthew Passion, BWV 244 | 1727 (revised for 1736 and 1742; score finished 1743 to 1746) | Two choirs, two orchestras, soloists. Each orchestra: 2 flutes, 2 oboes (also oboe d'amore and oboe da caccia), strings, viola da gamba, continuo | about 165 | The model. The new work sets its text again for one voice and one orchestra | wp-smp; reference | R, K |
| J. S. Bach | St John Passion, BWV 245 | 1724 | Choir, soloists, one orchestra |  | The first Passion of Bach that we have complete: the opening chorus has a pedal note of 12 bars (measured) | wp-smp; uma-edition | R |
| J. S. Bach | Trauerode, BWV 198 | 1727 | Choir, soloists, 2 flutes, 2 oboes d'amore, strings, 2 violas da gamba, 2 lutes, continuo |  | The sound of the same year as the Passion: flutes, oboes d'amore, gambas, and lutes together | wp-bwv198; uma-edition | R |
| J. S. Bach | Vergnügte Ruh, beliebte Seelenlust, BWV 170 | 1726 | Alto alone; oboe d'amore, 2 violins, viola, obbligato organ, continuo | 24 | A complete work of Bach for one alto: five movements, arias and recitatives in turn, a pastoral first aria on repeated eighth notes | wp-bwv170 | R |
| J. S. Bach | Widerstehe doch der Sünde, BWV 54 | 1714 | Alto alone; 2 violins, 2 violas, continuo |  | The first church cantata of Bach for one voice. It starts with a dissonant chord. Low range and tessitura for the alto | wp-bwv54 | R |
| J. S. Bach | Ich habe genug, BWV 82 | 1727 | Bass alone (a version for soprano with a flute, about 1731); oboe, strings, continuo |  | A solo cantata of the year of the Passion: one voice with one obbligato instrument | wp-bwv82 | R |
| J. S. Bach | Tilge, Höchster, meine Sünden, BWV 1083 | 1740s | Soprano, alto, strings, continuo |  | Bach made a new work from a work of a different composer: Pergolesi's Stabat Mater with a German psalm text and more orchestral material | wp-bwv1083 | R |
| J. S. Bach | Canonic Variations on "Vom Himmel hoch", BWV 769 | 1747 | Organ |  | Five variations in canon on one chorale tune: the model for chorale and canon together | wp-bwv769 | R |
| J. S. Bach | The Musical Offering, BWV 1079 | 1747 | Keyboard and chamber ensemble |  | Canons and fugues on one given theme. One canon goes up one whole tone at each repeat | wp-musical-offering; reference | R, K |
| J. S. Bach | Mass in B minor, BWV 232: Crucifixus | by 1749 | Choir, 2 flutes, strings, continuo |  | A chorus on a ground bass that goes down by semitones: the bass has 70 percent repeated notes and 21 percent semitone moves (measured) | uma-edition; reference | R, K |
| Heinrich Schütz | Matthäus-Passion, SWV 479 | 1666 | Voices alone |  | The old form before Bach: the Gospel story with no instruments and no arias | reference | K |
| Antonio Vivaldi | Stabat Mater, RV 621 | 1712 | Alto alone; violins 1 and 2, violas, continuo |  | Passion music for one alto and strings. F minor; slow in all movements but the Amen; movements 4 to 6 have the music of movements 1 to 3 | wp-vivaldi-stabat | R |
| Antonio Vivaldi | Nisi Dominus, RV 608 | about 1715 | Alto alone; strings, organ or harpsichord |  | A long work for one alto. A contralto or a countertenor can sing the part | wp-nisi | R |
| G. B. Pergolesi | Stabat Mater | 1736 | Soprano, alto; violins 1 and 2, viola, continuo |  | Passion music for solo voices and a small string group | wp-pergolesi | R |
| Felix Mendelssohn | Performance of the St Matthew Passion in Berlin | 1829 | Singakademie, orchestra |  | The first well-known new version: Mendelssohn changed parts of the work for the taste of his time. A new version for a new time has a long history | wp-smp | R |
| Franz Liszt | Via crucis, S. 53 | 1878 to 1879 | Mixed choir, soloists, organ (or piano) |  | A late, bare Passion work with few forces | wp-via-crucis | R |
| Igor Stravinsky | Pulcinella | 1920 | Soprano, tenor, bass; chamber orchestra | 35 to 40 | Music of the 18th century with new rhythm, new harmony, and new colours: the old notes stay in view | wp-pulcinella; reference | R, K |
| Anton Webern | Fuga (Ricercata) a 6 voci, from The Musical Offering | 1935 | Orchestra |  | Each voice of the fugue goes from instrument to instrument in short pieces: the colours show the motifs | reference | K |
| Alban Berg | Violin Concerto | 1935 | Violin and large orchestra |  | A chorale of Bach in a twelve-note work. The last section is a set of chorale variations. The row has triads: its first three notes are a G minor triad | wp-berg-vc; reference | R, K |
| Igor Stravinsky | Chorale Variations on "Vom Himmel hoch" | 1956 | Choir and orchestra |  | Bach's canons with new lines added: old counterpoint and new counterpoint in one texture | reference | K |
| Krzysztof Penderecki | St Luke Passion | 1966 | Soloists, choirs, orchestra |  | Almost fully atonal; a major triad comes only two times. The last chord is E major. A plain triad is a strong event after dissonance | wp-penderecki-luke | R |
| Arvo Pärt | Credo | 1968 | Piano, choir, orchestra | 12 | Collage: old tonal music against twelve-note music | wp-credo; reference | R, K |
| Alfred Schnittke | Concerto Grosso No. 1 | 1977 | 2 violins, keyboards, strings |  | A baroque form with more than one style at the same time (polystylism) | wp-schnittke-cg1 | R |
| Arvo Pärt | Cantus in Memoriam Benjamin Britten | 1977 | String orchestra and bell | 6.5 | A canon in A minor on one motif. It starts and ends with written silence | wp-cantus | R |
| Arvo Pärt | Fratres | 1977 | Three parts; no fixed instruments |  | Variations on a theme of six bars: "frantic activity and sublime stillness" | wp-fratres | R |
| Sofia Gubaidulina | Offertorium | 1980 (revised 1982 and 1986) | Violin and orchestra |  | A theme of Bach loses one note at each end in each variation. At the end the theme comes back note by note, backwards | wp-offertorium | R |
| Arvo Pärt | Passio (St John Passion) | 1982 | Bass (Jesus), tenor (Pilate), vocal quartet (Evangelist), choir, violin, oboe, cello, bassoon, organ | 70 | The text makes the rhythm. Each person has a note value and a pitch centre. One voice goes by step, one voice has the notes of a triad | wp-passio | R |
| Mauricio Kagel | Sankt-Bach-Passion | 1985 | Soloists, narrator, choirs, organ, orchestra |  | The form of the Passions of Bach with a different story (the life of Bach) | wp-kagel | R |
| Knut Nystedt | Immortal Bach, op. 153 | 1988 | Choir in many parts |  | One chorale phrase of Bach; then each voice sings the same phrase in a different tempo. All voices wait at the end of the phrase | wp-immortal-bach | R |
| Steve Reich | Proverb | 1995 | 3 sopranos, 2 tenors, 2 vibraphones, 2 electric organs |  | Canons on one short text, with the sound of medieval polyphony | wp-proverb | R |
| Osvaldo Golijov | La Pasión según San Marcos | 2000 | Soloists, choir, orchestra with Latin and African percussion |  | One of four new Passions for the Bach year 2000 (with Rihm, Gubaidulina, and Tan Dun). A Passion can speak in the musical language of its composer | wp-golijov | R |
| Sofia Gubaidulina | Johannes-Passion | 2000 | 4 soloists, 2 choirs, organ, orchestra |  | The Gospel text together with a second text (the Book of Revelation) | wp-gubaidulina-jp | R |
| Tan Dun | Water Passion after St Matthew | 2000 | Soloists, choir, strings, percussion with water |  | A Passion after Matthew for the same project: ritual sounds in place of the baroque orchestra | wp-golijov; reference | R, K |
| David Lang | the little match girl passion | 2007 | 4 voices (soprano, alto, tenor, bass); each singer plays simple percussion | 35 | The format of the St Matthew Passion with 15 numbers in 35 minutes: story numbers and response numbers in turn. "There is no Bach in my piece" | lang-note; wp-lmgp | R |
| Caroline Shaw | Punctum | 2009 (revised 2013; string orchestra 2022) | String quartet | 9 | The Passion chorale of the St Matthew Passion comes into view at about the middle. "Saturating the palette with classicism while denying it form" | bso-punctum | R |
| Max Richter | Recomposed: Vivaldi – The Four Seasons | 2012 | Violin and string orchestra |  | Richter removed 75 percent of the material of Vivaldi. The parts that stay are in loops and in phase shifts | wp-richter | R |
| Caroline Shaw | Partita for 8 Voices | 2009 to 2012 | 8 voices |  | The movement types of the baroque suite with the vocal sounds of today | wp-partita; reference | R, K |
| Caroline Shaw | Is a Rose | 2016 to 2019 | Mezzo-soprano and baroque orchestra (Philharmonia Baroque) |  | Three new songs for one mezzo-soprano and an orchestra of period instruments. The orchestra asks for new music for old instruments since 2016 | pbo-shaw | R |
| Caroline Shaw | The Listeners | 2019 | 2 soloists (low voices), chorus, baroque orchestra |  | A large new work for voices and an orchestra of period instruments | pbo-shaw | R |

Data file: [`research/tables/works.csv`](../research/tables/works.csv)

### S2. The movements of the St Matthew Passion

One row for each section. NBA is the number of the Neue Bach-Ausgabe; the letters divide a movement into its sections. Voices: Ev = Evangelist, Ch I and Ch II = the two choirs, S A T B = the four voice types. Instruments: Ft = flute, Ob = oboe, Oa = oboe d'amore, Oc = oboe da caccia, Vn = violin, Vs = solo violin, Va = viola, Vg = viola da gamba, Bc = continuo.

| Nba | Form | Voices | Key | Metre | Instruments | First words | Text from |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | chorus with a chorale | Chorale S, Ch I, Ch II | E minor | 12/8 | 2Ft 2Ob 2Vn Va Bc | Kommt, ihr Töchter, helft mir klagen + chorale O Lamm Gottes, unschuldig as cantus firmus | Picander + Nicolaus Decius |
| 2 | Gospel recitative | Ev, Jesus | G major to B minor | 4/4 | 2Vn Va Bc | Da Jesus diese Rede vollendet hatte | Mt 26:1–2 |
| 3 | chorale | Chorale | B minor | 4/4 | 2Ft 2Ob 2Vn Va Bc | Herzliebster Jesu | Johann Heermann |
| 4a | Gospel recitative | Ev | D major to C major | 4/4 | Bc | Da versammleten sich die Hohenpriester | Mt 26:3–4 |
| 4b | chorus of the crowd | Ch I, Ch II | C major | 4/4 | 2Ft 2Ob 2Vn Va Bc | Ja nicht auf das Fest | Mt 26:5 |
| 4c | Gospel recitative | Ev | C major to A minor | 4/4 | Bc | Da nun Jesus war zu Bethanien | Mt 26:6–8a |
| 4d | chorus of the crowd | Ch I | A minor to D minor | 4/4 | 2Ft 2Ob 2Vn Va Bc | Wozu dienet dieser Unrat | Mt 26:8b–9 |
| 4e | Gospel recitative | Ev, Jesus | B-flat major to E minor | 4/4 | 2Vn Va Bc | Da das Jesus merkete | Mt 26:10–13 |
| 5 | recitative with instruments | Rec A | B minor to F-sharp minor | 4/4 | 2Ft Bc | Du lieber Heiland du | Salomo Franck |
| 6 | aria | Aria A | F-sharp minor | 3/8 | 2Ft Bc | Buß und Reu | Picander |
| 7 | Gospel recitative | Ev, Judas | D major to B minor | 4/4 | Bc | Da ging hin der Zwölfen einer | Mt 26:14–16 |
| 8 | aria | Aria S | B minor | 4/4 | 2Ft 2Vn Va Bc | Blute nur, du liebes Herz! | Picander |
| 9a | Gospel recitative | Ev | G major | 4/4 | Bc | Aber am ersten Tage der süßen Brot | Mt 26:17a |
| 9b | chorus of the crowd | Ch I | G major | 3/4 | 2Ft 2Ob 2Vn Va Bc | Wo willst du, daß wir dir bereiten | Mt 26:17b |
| 9c | Gospel recitative | Ev, Jesus | G major to C major | 4/4 | 2Vn Va Bc | Er sprach: Gehet hin in die Stadt | Mt 26:18–21 |
| 9d | Gospel recitative | Ev | B-flat minor to F minor | 4/4 | Bc | Und sie wurden sehr betrübt | Mt 26:22a |
| 9e | chorus of the crowd | Ch I | F minor to C minor | 4/4 | 2Ft 2Ob 2Vn Va Bc | Herr, bin ich's? | Mt 26:22b |
| 10 | chorale | Chorale | A-flat major | 4/4 | 2Ob 2Vn Va Bc | Ich bin's, ich sollte büßen | Paul Gerhardt |
| 11 | Gospel recitative | Ev, Jesus, Judas | F minor to G major | 4/4–6/4 | 2Vn Va Bc | Er antwortete und sprach | Mt 26:23–29 |
| 12 | recitative with instruments | Rec S | E minor to C major | 4/4 | 2Oa Bc | Wiewohl mein Herz in Tränen schwimmt | Picander |
| 13 | aria | Aria S | G major | 6/8 | 2Oa Bc | Ich will dir mein Herze schenken | Picander |
| 14 | Gospel recitative | Ev, Jesus | B minor to E major | 4/4 | 2Vn Va Bc | Und da sie den Lobgesang gesprochen hatten | Mt 26:30–32 |
| 15 | chorale | Chorale | E major | 4/4 | 2Ft 2Ob 2Vn Va Bc | Erkenne mich, mein Hüter | Paul Gerhardt |
| 16 | Gospel recitative | Ev, Jesus, Peter | A major to G minor | 4/4 | 2Vn Va Bc | Petrus aber antwortete | Mt 26:33–35 |
| 17 | chorale | Chorale | E-flat major | 4/4 | 2Ob 2Vn Va Bc | Ich will hier bei dir stehen | Paul Gerhardt |
| 18 | Gospel recitative | Ev, Jesus | F major to A-flat major | 4/4 | 2Vn Va Bc | Da kam Jesus mit ihnen zu einem Hofe | Mt 26:36–38 |
| 19 | recitative with instruments | Rec T, Ch II Chorale | F minor to G major | 4/4 | 2Fl 2Oc 2Vn Va Bc | O Schmerz! Hier zittert das gequälte Herz | Picander + Johann Heermann |
| 20 | aria | Aria T, Ch II | C minor | 4/4 | 2Ft Ob 2Vn Va Bc | Ich will bei meinem Jesu wachen | Picander |
| 21 | Gospel recitative | Ev, Jesus | B major to G minor | 4/4 | 2Vn Va Bc | Und ging hin ein wenig | Mt 26:39 |
| 22 | recitative with instruments | Rec B | D minor to B-flat major | 4/4 | 2Vn Va Bc | Der Heiland fällt vor seinem Vater nieder | Picander |
| 23 | aria | Aria B | G minor | 3/8 | 2Vn Bc | Gerne will ich mich bequemen | Picander |
| 24 | Gospel recitative | Ev, Jesus | F major to B minor | 4/4 | 2Vn Va Bc | Und er kam zu seinen Jüngern | Mt 26:40–42 |
| 25 | chorale | Chorale | B minor | 4/4 | 2Ft 2Ob 2Vn Va Bc | Was mein Gott will, das g'scheh allzeit | Albert, Duke of Prussia |
| 26 | Gospel recitative | Ev, Jesus, Judas | D major to G major | 4/4 | 2Vn Va Bc | Und er kam und fand sie aber schlafend | Mt 26:43–50 |
| 27a | aria | Aria S A, Ch II | E minor | 4/4 | 2Ft 2Ob 2Vn Va Bc | So ist mein Jesus nun gefangen | Picander |
| 27b | chorus | Ch I, Ch II | E minor | 3/8 | 2Ft 2Ob 2Vn Va Bc | Sind Blitze, sind Donner in Wolken verschwunden? | Barthold Heinrich Brockes |
| 28 | Gospel recitative | Ev, Jesus | F-sharp major to C-sharp minor | 4/4 | 2Vn Va Bc | Und siehe, einer aus denen | Mt 26:51–56 |
| 29 | chorale fantasia | Chorale fantasia | E major | 4/4 | 2Ft 2Oa 2Vn Va Bc | O Mensch, bewein dein Sünde groß | Sebald Heyden |
| 30 | aria | Aria A, Ch II | B minor | 3/8 | Ft Oa 2Vn Va Bc | Ach! nun ist mein Jesus hin! | Picander |
| 31 | Gospel recitative | Ev | B major to D minor | 4/4 | Bc | Die aber Jesum gegriffen hatten | Mt 26:57–60a |
| 32 | chorale | Chorale | B-flat major | 4/4 | 2Ft 2Ob 2Vn Va Bc | Mir hat die Welt trüglich gericht' | Adam Reusner |
| 33 | Gospel recitative | Ev, 2 witnesses, high priest | G minor | 4/4 | Bc | Und wiewohl viel falsche Zeugen herzutraten | Mt 26:60b–63a |
| 34 | recitative with instruments | Rec T | A major to A minor | 4/4 | 2Ob Vg Bc | Mein Jesus schweigt | Picander |
| 35 | aria | Aria T | A minor | 4/4 | Vg Bc | Geduld! Wenn mich falsche Zungen stechen | Picander |
| 36a | Gospel recitative | Ev, Jesus, high priest | E minor | 4/4 | 2Vn Va Bc | Und der Hohepriester antwortete | Mt 26:63b–66a |
| 36b | chorus of the crowd | Ch I, Ch II | G major | 4/4 | 2Ft 2Ob 2Vn Va Bc | Er ist des Todes schuldig! | Mt 26:66b |
| 36c | Gospel recitative | Ev | C major to D minor | 4/4 | Bc | Da speieten sie aus | Mt 26:67 |
| 36d | chorus of the crowd | Ch I, Ch II | D minor to F major | 4/4 | 2Ft 2Ob 2Vn Va Bc | Weissage uns, Christe | Mt 26:68 |
| 37 | chorale | Chorale | F major | 4/4 | 2Ft 2Ob 2Vn Va Bc | Wer hat dich so geschlagen | Paul Gerhardt |
| 38a | Gospel recitative | Ev, Peter, 2 maids | A major to D major | 4/4 | Bc | Petrus aber saß draußen | Mt 26:69–73a |
| 38b | chorus of the crowd | Ch II | D major to A major | 4/4 | 2Ft Ob 2Vn Va Bc | Wahrlich, du bist auch einer | Mt 26:73b |
| 38c | Gospel recitative | Ev, Peter | C-sharp major to F-sharp minor | 4/4 | Bc | Da hub er an, sich zu verfluchen | Mt 26:74–75 |
| 39 | aria | Aria A | B minor | 12/8 | Vs 2Vn Va Bc | Erbarme dich | Picander |
| 40 | chorale | Chorale | F-sharp minor to A major | 4/4 | 2Ft 2Ob 2Vn Va Bc | Bin ich gleich von dir gewichen | Johann Rist |
| 41a | Gospel recitative | Ev, Judas | F-sharp minor to B major | 4/4 | Bc | Des Morgens aber hielten alle Hohepriester | Mt 27:1–4a |
| 41b | chorus of the crowd | Ch I, Ch II | B major to E minor | 3/4 | 2Ft 2Ob 2Vn Va Bc | Was gehet uns das an? | Mt 27:4b |
| 41c | Gospel recitative | Ev, 2 high priests | A minor to B minor | 4/4 | Bc | Und er warf die Silberlinge in den Tempel | Mt 27:5–6 |
| 42 | aria | Aria B | G major | 4/4 | Vs 2Vn Va Bc | Gebt mir meinen Jesum wieder! | Picander |
| 43 | Gospel recitative | Ev, Jesus, Pilate | E minor to D major | 4/4 | 2Vn Va Bc | Sie hielten aber einen Rat | Mt 27:7–14 |
| 44 | chorale | Chorale | D major | 4/4 | 2Ft 2Ob 2Vn Va Bc | Befiehl du deine Wege | Paul Gerhardt |
| 45a | Gospel recitative | Ev, Pilate, his wife, Ch I, Ch II | E major to A minor | 4/4 | Bc | Auf das Fest aber hatte der Landpfleger Gewohnheit | Mt 27:15–22a |
| 45b | chorus of the crowd | Ch I & II | A minor to B major | 4/4 | 2Ft 2Ob 2Vn Va Bc | Laß ihn kreuzigen! | Mt 27:22b |
| 46 | chorale | Chorale | B minor | 4/4 | 2Ft 2Ob 2Vn Va Bc | Wie wunderbarlich ist doch diese Strafe! | Johann Heermann |
| 47 | Gospel recitative | Ev, Pilate | B minor | 4/4 | Bc | Der Landpfleger sagte | Mt 27:23a |
| 48 | recitative with instruments | Rec S | E minor to C major | 4/4 | 2Oc Bc | Er hat uns allen wohlgetan | Picander |
| 49 | aria | Aria S | A minor | 3/4 | Ft 2Oc | Aus Liebe will mein Heiland sterben | Picander |
| 50a | Gospel recitative | Ev | E minor | 4/4 | Bc | Sie schrieen aber noch mehr | Mt 27:23b |
| 50b | chorus of the crowd | Ch I & II | B minor to C-sharp major | 4/4 | 2Ft 2Ob 2Vn Va Bc | Laß ihn kreuzigen! | Mt 27:23c |
| 50c | Gospel recitative | Ev, Pilate | C-sharp major to B minor | 4/4 | Bc | Da aber Pilatus sahe | Mt 27:24–25a |
| 50d | chorus of the crowd | Ch I & II | B minor to D major | 4/4 | 2Ft 2Ob 2Vn Va Bc | Sein Blut komme über uns | Mt 27:25b |
| 50e | Gospel recitative | Ev | D major to E minor | 4/4 | Bc | Da gab er ihnen Barrabam los | Mt 27:26 |
| 51 | recitative with instruments | Rec A | F major to G minor | 4/4 | 2Vn Va Bc | Erbarm es Gott! | Picander |
| 52 | aria | Aria A | G minor | 3/4 | 2Vn Bc | Können Tränen meiner Wangen | Picander |
| 53a | Gospel recitative | Ev | F major to D minor | 4/4 | Bc | Da nahmen die Kriegsknechte | Mt 27:27–29a |
| 53b | chorus of the crowd | Ch I, Ch II | D minor to A major | 4/4 | 2Ft 2Ob 2Vn Va Bc | Gegrüßet seist du, Jüdenkönig! | Mt 27:29b |
| 53c | Gospel recitative | Ev | D minor | 4/4 | Bc | Und speieten ihn an | Mt 27:30 |
| 54 | chorale | Chorale | D minor to F major | 4/4 | 2Ft 2Ob 2Vn Va Bc | O Haupt voll Blut und Wunden | Paul Gerhardt |
| 55 | Gospel recitative | Ev | A minor | 4/4 | Bc | Und da sie ihn verspottet hatten | Mt 27:31–32 |
| 56 | recitative with instruments | Rec B | F major to D minor | 4/4 | 2Ft Vg Bc | Ja freilich will in uns | Picander |
| 57 | aria | Aria B | D minor | 4/4 | Vg Bc | Komm, süßes Kreuz | Picander |
| 58a | Gospel recitative | Ev | C major to F-sharp major | 4/4 | Bc | Und da sie an die Stätte kamen | Mt 27:33–39 |
| 58b | chorus of the crowd | Ch I, Ch II | F-sharp major to B minor | 4/4 | 2Ft 2Ob 2Vn Va Bc | Der du den Tempel Gottes zerbrichst | Mt 27:40 |
| 58c | Gospel recitative | Ev | F-sharp major to E minor | 4/4 | Bc | Desgleichen auch die Hohenpriester | Mt 27:41 |
| 58d | chorus of the crowd | Ch I, Ch II | E minor | 4/4 | 2Ft 2Ob 2Vn Va Bc | Andern hat er geholfen | Mt 27:42–43 |
| 58e | Gospel recitative | Ev | G major to C minor | 4/4 | Bc | Desgleichen schmäheten ihn | Mt 27:44 |
| 59 | recitative with instruments | Rec A | A-flat major | 4/4 | 2Oc Bc | Ach Golgatha | Picander |
| 60 | aria | Aria A, Ch II | E-flat major | 4/4 | 2Ob 2Oc 2Vn Va Bc | Sehet, Jesus hat die Hand | Picander |
| 61a | Gospel recitative | Ev, Jesus | E-flat major to C minor | 4/4 | Bc | Und von der sechsten Stunde an | Mt 27:45–47a |
| 61b | chorus of the crowd | Ch I | C minor to F major | 4/4 | 2Ob 2Vn Va Bc | Der rufet dem Elias! | Mt 27:47b |
| 61c | Gospel recitative | Ev | F major to G minor | 4/4 | Bc | Und bald lief einer unter ihnen | Mt 27:48–49a |
| 61d | chorus of the crowd | Ch II | G minor to D minor | 4/4 | 2Ft Ob 2Vn Va Bc | Halt! laß sehen | Mt 27:49b |
| 61e | Gospel recitative | Ev | D minor to A minor | 4/4 | Bc | Aber Jesus schriee abermal laut | Mt 27:50 |
| 62 | chorale | Chorale | A minor | 4/4 | 2Ft 2Ob 2Vn Va Bc | Wenn ich einmal soll scheiden | Paul Gerhardt |
| 63a | Gospel recitative | Ev | C major to A-flat major | 4/4 | Bc | Und siehe da, der Vorhang im Tempel zerriß | Mt 27:51–54a |
| 63b | chorus of the crowd | Ch I & II | A-flat major | 4/4 | 2Ft Ob 2Vn Va Bc | Wahrlich, dieser ist Gottes Sohn gewesen | Mt 27:54b |
| 63c | Gospel recitative | Ev | E-flat major to B-flat major | 4/4 | Bc | Und es waren viel Weiber da | Mt 27:55–59 |
| 64 | recitative with instruments | Rec B | G minor | 4/4 | 2Vn Va Bc | Am Abend, da es kühle war | Salomo Franck |
| 65 | aria | Aria B | B-flat major | 12/8 | 2Oc 2Vn Va Bc | Mache dich, mein Herze, rein | Picander |
| 66a | Gospel recitative | Ev | G minor to E-flat major | 4/4 | Bc | Und Joseph nahm den Leib | Mt 27:59–62 |
| 66b | chorus of the crowd | Ch I, Ch II | E-flat major to D major | 4/4 | 2Ft 2Ob 2Vn Va Bc | Herr, wir haben gedacht | Mt 27:63–64 |
| 66c | Gospel recitative | Ev, Pilate | G minor to E-flat major | 4/4 | Bc | Pilatus sprach zu ihnen | Mt 27:65–66 |
| 67 | recitative with instruments | Rec S A T B, Ch II | E-flat major to C minor | 4/4 | 2Ft 2Ob 2Vn Va Bc | Nun ist der Herr zur Ruh gebracht | Picander |
| 68 | chorus | Ch I, Ch II | C minor | 3/4 | 2Ft 2Ob 2Vn Va Bc | Wir setzen uns mit Tränen nieder | Picander |

Data file: [`research/tables/bach_movements.csv`](../research/tables/bach_movements.csv)

### S3. Elements of the St Matthew Passion

The table lists the elements of the work of Bach that the new work can use.

| Element | Where | Content | Parameters | Source | Evidence |
| --- | --- | --- | --- | --- | --- |
| Three layers of text | The full work | The Gospel text (the story), the poems of Picander (the response of one person), and the chorales (the response of the congregation) | Sections: 43 Gospel recitatives, 18 choruses of the crowd, 15 arias, 11 recitatives with instruments, 12 plain chorales, 4 large choruses | wp-smp-structure | R |
| Two parts | The full work | Part 1 has movements 1 to 29, part 2 has movements 30 to 68. A sermon was between the parts | 29 + 39 movements | wp-smp-structure | R |
| Sixteen scenes | The full work | A scene starts with Gospel text and ends on an aria, a chorale, or a chorus. The two parts start with a chorus or an aria | 16 scenes; the booklet of one recording gives 9 larger scenes | wp-smp-structure | R |
| Opening chorus | Movement 1 | Two choirs in dialogue ("Sehet!" - "Wen?"), and above them the chorale "O Lamm Gottes, unschuldig" as a third layer | E minor, 12/8. The chorale is in G major. In the first version an instrument played the chorale | wp-smp-structure; wp-smp | R |
| Pulse of the opening | Movement 1 | The bass voice starts on E and goes up by step in the rhythm quarter, eighth | e, fis, g, then fis and gis to a: the line of bar 17 in the bass | commons-incipits | R |
| Evangelist | 43 sections | A tenor tells the story in recitative with continuo only. Each syllable has one note | First phrases of four sections: from E-flat 3 to B-flat 4, in eighth notes and sixteenth notes | wp-smp; wp-evangelist; commons-incipits | R |
| Voice of Christ | Movements 2, 4e, 9c, 11, 14, 16, 18, 21, 24, 26, 28, 36a, 43 | The words of Jesus have long chords of the strings around them: the "halo" | Instruments of these sections: 2 violins, viola, continuo | wp-smp; wp-smp-structure | R |
| The halo stops | Movement 61a | Only the last words ("Eli, Eli, lama asabthani?") have no strings | Instruments of the section: continuo only | wp-smp; wp-smp-structure | R |
| Chorus of the crowd | 18 sections | The words of groups. The two choirs sing in turns, or together, or one choir alone (the disciples are always choir 1) | Short: 5 to 18 bars in five sections of the incipit data | wp-smp; commons-incipits | R |
| Lass ihn kreuzigen | Movements 45b and 50b | A fugue subject with the shape of a cross. The second time it is one whole tone higher | 45b: A minor to B major. 50b: B minor to C-sharp major. Subject: A, A, G-sharp, C, B, D-sharp, A, G, F-sharp, G, A, B-flat | wp-smp-structure; commons-incipits | R |
| Wahrlich | Movement 63b | "Truly, this was the Son of God": the two choirs together, as one voice | 2 bars in A-flat major | wp-smp-structure; uma-edition | R |
| The Passion chorale | Movements 15, 17, 44, 54, 62 | The tune "Herzlich tut mich verlangen" comes five times with different words and chords | Keys: E major, E-flat major, D major, D minor to F major, A minor. The last setting ends on the dominant (measured) | wp-smp-structure; sapp-chorales | R |
| Herzliebster Jesu | Movements 3, 19, 46 | The first chorale of the work comes three times. In movement 19 the choir sings it between the lines of the tenor | Keys: B minor; F minor to G major; B minor | wp-smp-structure | R |
| Chorale as an answer | Movements 9e and 10 | The disciples ask "Herr, bin ich's?". The chorale answers: "Ich bin's, ich sollte büßen" | Chorus in F minor to C minor; chorale in A-flat major | wp-smp; wp-smp-structure | R |
| Recitative with instruments before an aria | 10 pairs | A short free movement with one fixed figure in the instruments. The aria follows with the same voice | Example: movement 5, flutes in thirds above a plucked bass | wp-smp; commons-incipits | R |
| Aria with one solo instrument | Movements 39, 42, 35, 57, 49 | The instrument is an equal partner of the voice | Erbarme dich: the violin has 2.2 notes for each quarter note, the alto has 0.9 (measured) | wp-smp; uma-edition | R |
| Aria with no bass | Movement 49 | "Aus Liebe will mein Heiland sterben": flute and two oboes da caccia; no strings and no continuo | A minor, 3/4. The oboes da caccia have repeated quarter notes, staccato | wp-smp; uma-edition | R |
| Aria with choir | Movements 20, 27a, 30, 60 | One voice sings; the second choir answers with questions or calls ("Wohin?") |  | wp-smp-structure; wp-smp | R |
| Siciliano in 12/8 | Movements 1, 39, 65 | The three movements in 12/8: the opening chorus, "Erbarme dich", and "Mache dich, mein Herze, rein" | Keys: E minor, B minor, B-flat major | wp-smp-structure | R |
| Sarabande at the end | Movement 68 | The last chorus is a slow dance in 3/4 in da capo form. The last chord of C minor has the note B above it, which goes to C | C minor; 128 bars with the repeat in the edition | wp-smp; uma-edition | R |
| Tears and blows in the instruments | Movements 6, 51 | Flutes play staccato when the alto sings of tears that fall. A dotted rhythm without pause shows the scourging | Movement 51: a dotted sixteenth and a thirty-second, 16 times in one bar | wp-smp; commons-incipits | R |
| Thunder and earthquake | Movements 27b and 63a | A fast chorus in 3/8 on a bass theme of broken chords. In 63a the continuo has runs of thirty-second notes | 27b: E minor, 3/8; the theme starts in the bass | wp-smp-structure; commons-incipits | R |
| Sharp keys and flat keys | The full work | The work starts in E minor (one sharp) and ends in C minor (three flats). The death scene is in the flat keys | First key E minor; last key C minor; movement 59: A-flat major; movement 63b: A-flat major | wp-smp-structure | R |
| Time signatures | The full work | Almost all Gospel text is in 4/4. The arias and the large choruses have the other metres | 12/8: 3 movements. 3/8: 4. 3/4: 5. 6/8: 1. 6/4: a part of movement 11 | wp-smp-structure | R |
| Instruments as colours | The full work | Each aria has its own instruments. Recorders come in one movement only; the viola da gamba in four | Recorders: 19. Oboes da caccia: 19, 48, 49, 59, 60, 65. Viola da gamba: 34, 35, 56, 57. Solo violin: 39, 42 | wp-smp-structure | R |
| The alto movements | Movements 5, 6, 27a, 30, 39, 51, 52, 59, 60 | The alto has three arias, two arias with the second choir, three recitatives with instruments, and one duet with the soprano | Keys of the arias: F-sharp minor, B minor, B minor, G minor, E-flat major | wp-smp-structure | R |
| No word of the Resurrection | The full work | The story ends at the tomb. The last words are "Ruhe sanfte, sanfte ruh" |  | wp-smp; bischof-244 | R |
| Lute and viola da gamba | First version | In the first version the first choir had a lute. Later the viola da gamba has its part |  | wp-smp | R |

Data file: [`research/tables/bach_elements.csv`](../research/tables/bach_elements.csv)

### S4. Motifs of the St Matthew Passion

The notes are in the music language of the project: `c'` is middle C, a `'` is one octave up, a `,` is one octave down, `is` is a sharp, `es` is a flat, and a number is a note value (`8` = eighth note). A test makes sure that each line of notes is correct text of this language.

| Name | Movement | Key | Metre | Line | Notes | Words | Character | Source | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Kommt ihr Töchter: theme | 1, bar 17 | E minor | 12/8 | soprano of choir 1 | `e'8[ g' b'] e''4.~ e''8[ dis''] cis'' dis''[ b'] c'' d''4 d''8 c''[ b' a'] dis''[ b' dis''] e''4 fis''8` | Kommt, ihr Töchter, helft mir klagen | A broken chord up, then a long note and a turn around the fifth | commons-incipits | R |
| Kommt ihr Töchter: bass | 1, bar 17 | E minor | 12/8 | bass of choir 1 | `e4.~ e8[ fis] g fis4 fis8 fis[ gis] a gis[ fis e] a4.~ a8[ g] fis g4 fis8` | Kommt, ihr Töchter, helft mir klagen | A slow step up from the key note in the rhythm long, short | commons-incipits | R |
| O Lamm Gottes unschuldig: tune | 1 | G major | 4/4 | cantus firmus | `g'4 g' g' d'' d'' e''2 d''4\fermata d''4 g' a' b' c'' b' a'8 g' g'4\fermata b'4 b' b' a' b' g'8 fis' e'4 d'\fermata d''4 e'' d'' d'' b'8 c'' d''4 c'' b'\fermata e''4 d''8 c'' b'4 a' b' d'' b' a'2 g'2.\fermata` | O Lamm Gottes, unschuldig am Stamm des Kreuzes geschlachtet | The tune of the edition of the chorales (BWV 401), moved from F major to the key of the Passion | sapp-chorales | M |
| Du lieber Heiland du: flutes | 5 | B minor | 4/4 | 2 flutes | `<d'' fis''>16( <cis'' e''> <b' d''>) <e'' g''>-. <d'' fis''>( <cis'' e''> <b' d''>) <d'' fis''>-.` |  | Thirds that fall as drops; the bass has plucked quarter notes | commons-incipits | R |
| Du lieber Heiland du: voice | 5 | B minor | 4/4 | alto | `r4 r8 fis' ais'8. b'16 cis''8 fis' d''4 r` | Du lieber Heiland du | Recitative of the alto: a leap up of a sixth to the last word | commons-incipits | R |
| Buß und Reu: voice | 6, bar 13 | F-sharp minor | 3/8 | alto | `cis''8[ d''] cis'' bis'4. b'32[( cis'' d''16 cis''8]) b' ais'4. b'8 a'[( gis']) a' fis'[( eis']) fis' \appoggiatura { e'8 } d'4 cis'8` | Buß und Reu, Buß und Reu knirscht das Sündenherz entzwei | A semitone turn on each of the two words, then a slow fall of an octave | commons-incipits; wp-smp | R |
| Buß und Reu: bass | 6, bar 13 | F-sharp minor | 3/8 | continuo | `fis4.~ fis8 gis16( fis eis dis) eis4. e8 fis16( e d cis) d8( cis b,) cis4.~ cis8 b,16( a, gis, fis,) eis,8` |  | The bass goes down by semitones on the long notes: F-sharp, E-sharp, E, D, C-sharp | commons-incipits | R |
| Buß und Reu: flutes | 6, bar 13 | F-sharp minor | 3/8 | 2 flutes | `r4. <dis'' gis''>8-.( <dis'' gis''>-. <dis'' gis''>-.) r4. <cis'' fis''>8-.( <cis'' fis''>-. <cis'' fis''>-.)` |  | Three soft staccato notes in each second bar: the drops of the tears | commons-incipits; wp-smp | R |
| Erbarme dich: violin | 39 | B minor | 12/8 | solo violin | `fis'8 \grace { b'16 cis'' } d''8. cis''16 b'8 \grace { cis''8 } b'8. ais'16 b'8 b'4.~ b'4 b'8 g''8.( fis''32 g'' a''8~ a''8.) g''16 fis''8 \grace { fis''8 } e''4.~ e''8. g''16 e''8` |  | A leap up of a minor sixth from the fifth note of the key, with a slide; then steps down in the siciliano rhythm | uma-edition | R |
| Erbarme dich: voice | 39, bar 9 | B minor | 12/8 | alto | `fis'8 d''8. cis''16 b'8~ b'8. ais'16 b'8 b'2.~ b'4 e'8 e'[ dis'] a' g'4 e'8 g'4 b'8 c''4( b'8) b'4( ais'8) ais'4( b'8) cis''4.` | Erbarme dich, mein Gott, um meiner Zähren willen | The same leap of a sixth; then pairs of notes that sigh, a semitone down each time | uma-edition | R |
| Erbarme dich: bass | 39 | B minor | 12/8 | continuo (plucked) | `b,8 b b b a a a g g g fis fis fis e e e fis fis fis g e g b g b e' e' e' d' d' d' cis' cis' cis' ais ais ais b b b g g g fis cis e e ais, cis fis,4` |  | Three equal eighth notes on each note of a scale that goes down from B to E | uma-edition | R |
| Erbarm es Gott: strings | 51 | F major to G minor | 4/4 | strings | `<g' bes' e''>16. <e' g' c''>32 <g' bes' e''>16. <e' g' c''>32 <g' bes' e''>16. <e' g' c''>32 <g' bes' e''>16. <e' g' c''>32 <fis' a' es''>16. <a' c''>32 <fis' a' es''>16. <a' c''>32 <fis' a' es''>16. <a' c''>32 <fis' a' es''>16. <a' c''>32` |  | A dotted rhythm with no pause on dissonant chords: the blows of the scourge | commons-incipits; wp-smp | R |
| Erbarm es Gott: voice | 51 | F major to G minor | 4/4 | alto | `r8 c' bes'16[ a'] bes'8 a'4 r8 a' d'8. d'16 b' c'' d'' f' e'8 e' r` | Erbarm es Gott! Hier steht der Heiland angebunden | A leap up of a minor seventh on the first word | commons-incipits | R |
| Laß ihn kreuzigen: subject | 45b | A minor | 4/4 | bass | `a4 a gis8 c'4 b8 dis8 a4 g16[ fis] g8 a bes4~ bes8 a d' c'` | Laß ihn kreuzigen | Two equal notes, then a line that crosses itself: a diminished fourth up, a minor sixth down, a tritone up | commons-incipits | R |
| Laß ihn kreuzigen: second time | 50b | B minor | 4/4 | bass | `b4 b ais8 d'4 cis'8 eis8 b4 a16[ gis] a8 b c'4` | Laß ihn kreuzigen | The same subject, one whole tone higher | commons-incipits | R |
| Sind Blitze sind Donner: theme | 27b | E minor | 3/8 | bass | `r8 r fis b fis d fis d b, a b16 a g fis g8 e` | Sind Blitze, sind Donner in Wolken verschwunden | A broken chord down in equal eighth notes, fast | commons-incipits | R |
| O Schmerz: bass | 19 | F minor | 4/4 | continuo | `f16 f f f f f f f f f f f f f f f` |  | One note in sixteenth notes that does not stop: the heart that trembles | commons-incipits | R |
| O Schmerz: winds | 19 | F minor | 4/4 | recorders and oboes da caccia | `r8 <c'' as''>( <g' e''> <as' f''>)` |  | Sighs in pairs of parallel sixths | commons-incipits | R |
| Können Tränen: violins | 52 | G minor | 3/4 | violins in unison | `g'8.( bes'16) d'8.( g'16) bes8.( d'16) g'8.( bes'16) d'8.( g'16) bes8.( d'16) g'8( a'16 bes') c''( d'' es''8) es''16( d'' es''8) es''16( d'' c''8) a''4 r` |  | A dotted figure that goes down through the chord, bar after bar | uma-edition | R |
| Können Tränen: voice | 52, bar 13 | G minor | 3/4 | alto | `g'8 bes'16[ a'] g'[ fis' g'8]~ g'16[ fis'] g'8` | Können Tränen meiner Wangen | A turn around the key note; the voice starts as the instruments did | uma-edition | R |
| Aus Liebe: flute | 49 | A minor | 3/4 | flute | `a'4 e''4.~ e''32 f'' e'' d'' \grace { d''8 } e''8. c'''16 \grace { e''8 } d''2 b''4~ b''16 c'''( b'' a'') b''( a'' gis'' fis'' e'' d'' c'' b')` |  | A long note with a turn; then a leap up of a sixth and a line of sixteenth notes that falls | uma-edition | R |
| Aus Liebe: oboes da caccia | 49 | A minor | 3/4 | 2 oboes da caccia | `<a' c''>4-. <a' c''>-. <a' c''>-. <a' b'>-. <a' b'>-. <a' d''>-. <gis' d''>-. <gis' d''>-. <gis' b'>-.` |  | Repeated quarter notes, staccato; there is no bass instrument | uma-edition; wp-smp | R |
| Mache dich mein Herze rein: theme | 65 | B-flat major | 12/8 | violin 1 with oboe da caccia 1 | `r4. f'4( es'8) d'4( es'8) f'8( g') a' bes'4.` |  | Steps in the rhythm long, short, down and then up to the key note | uma-edition | R |
| Mache dich mein Herze rein: bass | 65 | B-flat major | 12/8 | continuo | `bes,4 bes8 bes4 bes,8 bes,4 bes8 bes4 bes,8` |  | Octave leaps on the key note in the rhythm long, short: a cradle | uma-edition | R |
| Wahrlich dieser ist Gottes Sohn gewesen: top line | 63b | A-flat major | 4/4 | oboe 1 and violin 1 | `c''8 as' f''4. es''16 des'' es''8 f''16 g'' as''8 g''16 f'' es''4. as'8 des''4 c''4` | Wahrlich, dieser ist Gottes Sohn gewesen | The full movement: two bars and one chord. A leap up of a sixth, then a climb to the octave | uma-edition | R |
| Wahrlich dieser ist Gottes Sohn gewesen: bass | 63b | A-flat major | 4/4 | continuo | `r4 as,8 f, des4. c16 bes, c8 bes, c des16 es f8 des bes, es as,4` |  | The bass of the two bars | uma-edition | R |
| Wir setzen uns: theme | 68, bar 13 | C minor | 3/4 | soprano | `es''8[ f''16 g''] f''8[ es''] d''[ c'']` | Wir setzen uns mit Tränen nieder | A small step up and a fall of a fourth, in the rhythm of a sarabande | uma-edition | R |
| Wir setzen uns: last three bars | 68 | C minor | 3/4 | flutes | `r4 r8 f'''8( es''' d''') b''8( c''') g''( f'' es'' d'') b''4( c'''2)` |  | The last chord is C minor. The flutes hold the note B above it for one quarter note before they go to C | uma-edition | R |
| Herzlich tut mich verlangen: tune | 62 | A minor | 4/4 | soprano | `e'4 a' g' f' e' d'2 e'4\fermata b'4 c'' b'8 c''16 d'' c''4 b'8 a' a'2.\fermata c''4 b'8 a' g'4 a' b' c''2 c''4\fermata g'4 a' g' a'8 g' f'4 e'2.\fermata c''4 b'8 c'' d''4 c'' b' a'2 b'4\fermata e'4 f' e' d' g'8 f' e'2.\fermata` | Wenn ich einmal soll scheiden | The tune as in the last setting, moved from the key of the edition (B minor) to the key of the Passion (A minor). The last note is E | sapp-chorales; wp-smp-structure | M |
| Herzlich tut mich verlangen: bass of the last setting | 62 | A minor | 4/4 | bass | `a8 g f4 e d c fis, g, c\fermata gis,4 a, d e e, a,2.\fermata a4 dis e es d e f c\fermata c4 f e8 d cis4 d a,2.\fermata fis4 g8 a b4 e8 fis g4 cis d g,\fermata c4 b, c bes,8 a, g,4 gis, a, e,\fermata` |  | The bass of Bach for the last setting: many semitones, and the end on the dominant | sapp-chorales | M |
| Evangelist: the darkness | 61a | E-flat major to C minor | 4/4 | tenor | `r4 r8 es g as bes c' des' bes g16 bes des' es' fes'8. fes'16 fes'4` | Und von der sechsten Stunde an ward eine Finsternis | A climb by step and by thirds to a note outside the key (F-flat) on the word for darkness | commons-incipits | R |
| Evangelist: the cry | 61e | D minor to A minor | 4/4 | tenor | `r8 a16 a d'8 d' f' d' b b16 b gis'8 r` | Aber Jesus schriee abermal laut | A leap up of a major sixth to the highest note on the last word | commons-incipits | R |
| Evangelist: the veil of the temple | 63a | C major | 4/4 | tenor | `r8 g c' e' g' r r g' bes' g'16 f' e'8 cis'16 d' a8` | Und siehe da, der Vorhang im Tempel zerriß | A broken major chord up; then a fall through a diminished chord | commons-incipits | R |
| Evangelist: the veil of the temple (continuo) | 63a | C major | 4/4 | continuo | `e,4 r r32 e,( f, g, a, b, c d) e8-. r r4 r16 b32( a g f e d) cis8-.` |  | Runs of thirty-second notes up and down: the veil that tears | commons-incipits | R |

Data file: [`research/tables/motifs.csv`](../research/tables/motifs.csv)

### S5. The chorales of the St Matthew Passion

Eight tunes come in 17 movements.

| Tune | Text | Movements | Keys in the passion | Setting | Use by bach | Source | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| O Lamm Gottes, unschuldig | Nikolaus Decius: a German form of the Agnus Dei | 1 | G major | A fixed line above the opening chorus (E minor) | The innocent lamb: the theme of the full work at its start | wp-smp-structure; wp-o-lamm | R |
| Herzliebster Jesu | Johann Heermann, 1630, stanzas 1, 3, and 4 | 3, 19, 46 | B minor; F minor to G major; B minor | Two plain settings; in movement 19 the lines of the chorale come between the lines of a tenor recitative | The question "what have you done?": at the start of the story and at the sentence | wp-smp-structure; wp-herzliebster | R |
| O Welt, ich muss dich lassen | Paul Gerhardt, "O Welt, sieh hier dein Leben", stanzas 5 and 3 | 10, 37 | A-flat major; F major | Two plain settings | "It is I": the answer of each listener to the question of the disciples | wp-smp-structure | R |
| Herzlich tut mich verlangen | Paul Gerhardt, "O Haupt voll Blut und Wunden", stanzas 5, 6, 1 and 2, 9; and "Befiehl du deine Wege", stanza 1 | 15, 17, 44, 54, 62 | E major; E-flat major; D major; D minor to F major; A minor | Five plain settings with different chords | The main chorale. The last time, after the death of Jesus, it is in the lowest key and ends on the dominant | wp-smp-structure; sapp-chorales | R |
| Was mein Gott will, das g'scheh allzeit | Albert, Duke of Prussia | 25 | B minor | Plain setting | After the prayer in Gethsemane | wp-smp-structure | R |
| O Mensch, bewein dein Sünde groß | Sebald Heyden, 1525: the oldest chorale of the work | 29 | E major | A large chorale movement at the end of part 1: the tune in the soprano, figures of sighs in the flutes | The close of part 1 | wp-smp-structure; wp-smp | R |
| In dich hab ich gehoffet, Herr | Adam Reusner, stanza 5 | 32 | B-flat major | Plain setting | After the false witnesses | wp-smp-structure | R |
| Werde munter, mein Gemüte | Johann Rist, stanza 6 | 40 | F-sharp minor to A major | Plain setting | After "Erbarme dich": the answer to the denial of Peter | wp-smp-structure | R |

Data file: [`research/tables/chorales.csv`](../research/tables/chorales.csv)

### S6. The voice and the instruments

The measured ranges come from tables M4 and M5. The ranges of this work are in the file `design/orchestra.toml`.

| Instrument | Facts | In the work of bach | In this work | Source | Evidence |
| --- | --- | --- | --- | --- | --- |
| Alto voice | The second-highest part in four-part music. Low voices of women (mezzo-soprano, contralto) and high voices of men (countertenor) sing it. A countertenor has a range from about E3 to D5 or E5 | Three arias of the corpus (measured): lowest note A3, highest note E5; the middle of the voice is A4; 90 percent of the time is between C-sharp 4 and D5 | Range G3 to F5 in the orchestra file. Usual notes B3 to D5; E5 and F5 only at peaks | wp-alto; wp-countertenor; uma-edition | R |
| Flute (flauto traverso) | The flute of the time of Bach has one key. Its lowest note is D4 | Flutes of the corpus (measured): from D4 to F-sharp 6; the middle is E5 | Range D4 to G6. The players also have recorders | uma-edition; reference | R, K |
| Recorder | The alto recorder in F | Only in movement 19 ("O Schmerz") | The flute players change to recorders for the most quiet numbers | wp-smp; reference | R, K |
| Oboe d'amore | In A: the sound is a minor third below the written note. Its tone is "less assertive and more tranquil" than the tone of the oboe; its bell has the form of a pear | Corpus (measured): from B-flat 3 to B5 | Each oboe player has an oboe d'amore | wp-oboe-damore; uma-edition | R |
| Oboe da caccia | In F: the sound is a fifth below the written note. A curved tube and a brass bell. Range from F3 to G5 | Movements 19, 48, 49, 59, 60, and 65. In movement 49 two of them are the only harmony. Corpus (measured): from F3 to E5 | Each oboe player has an oboe da caccia. The audio uses the English horn | wp-oboe-da-caccia; wp-smp-structure; uma-edition | R |
| Bassoon | The bass of the oboe group | A part of the continuo group | One player: continuo, and solo lines in some numbers | wp-smp-structure | R |
| Violin and viola | The baroque violin has a different neck, fingerboard, bridge, and bass bar, and gut strings | Violins of the corpus (measured): from G3 to E-flat 6. The solo violin of "Erbarme dich": from B3 to E6 | 4 first violins, 4 second violins, 3 violas. Highest note of the orchestra file: A6 for the violins | wp-hip; uma-edition | R |
| Viola da gamba | A bowed instrument with frets. Most viols have six strings tuned in fourths with a third in the middle. The player holds it between the legs | Movements 34, 35, 56, 57. Corpus, Trauerode (measured): from D2 to D5 | One player. A solo voice in the number of the cross | wp-viol; wp-smp-structure; uma-edition | R |
| Violoncello and violone | The word violone was used for different large bowed instruments, with three to six strings and sometimes with frets | The bass line of the continuo. Corpus (measured): the continuo is between C2 and G4 | 2 violoncellos and 1 violone. The violone sounds one octave below the written note | wp-violone; uma-edition | R |
| Theorbo | A lute with a long neck and a second pegbox. The first two strings are tuned one octave lower. It played basso continuo in the baroque period | The first version of the Passion has a lute. The Trauerode has two lutes | One player: chords and plucked bass notes. The audio uses the harp | wp-theorbo; wp-smp; wp-bwv198 | R |
| Harpsichord and organ | The chord instruments of the continuo play from a bass line with figures: the player makes the chords | The organ is the usual chord instrument of the Passion. Most frequent figures of the corpus (measured): 6, 6 4, 6 5, 7 with a raised third, 5, 7 | One organ (long chords) and one harpsichord (short chords, recitative) | wp-figured-bass; uma-edition | R |
| No trumpets and no timpani | The orchestra of the Passion has woodwinds, strings, and continuo only | All movements | The same | wp-smp-structure | R |

Data file: [`research/tables/instruments.csv`](../research/tables/instruments.csv)

### S7. Devices of counterpoint and form

The first part of the table has the devices of the time of Bach. The second part has devices of later music that the study team examined for the new work.

| Device | Period | Content | Parameters | Example | Source | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Chorale as a fixed line (cantus firmus) | Baroque | A chorale tune in long notes is one layer. The other voices have their own material around it | Bach, movement 1: chorale in G major above a chorus in E minor | St Matthew Passion, movements 1 and 29 | wp-smp-structure; wp-chorale-fantasia | R |
| Canon on a chorale | Baroque | A line imitates itself at a fixed distance in time and pitch, while a chorale tune goes through the texture | Five variations in canon | Bach, Canonic Variations on "Vom Himmel hoch", BWV 769 | wp-bwv769 | R |
| Canon that goes up by step | Baroque | The canon ends one whole tone higher than it started. Each repeat is one tone higher | Six repeats bring the canon back to the first key, one octave higher | Bach, The Musical Offering, the canon "per tonos" | reference | K |
| Fugue subject and stretto | Baroque | Voices enter one after the other with the same subject. In a stretto "the answer enters before the subject is completed" |  | St Matthew Passion, "Laß ihn kreuzigen" | wp-stretto; commons-incipits | R |
| Ground bass | Baroque | A short bass line repeats. The upper voices change above it | The form is usually serious and in triple metre | Bach, Crucifixus of the Mass in B minor; Purcell, Dido's lament | wp-passacaglia; reference | R, K |
| Lament bass | Baroque | A bass that goes down a fourth from the key note to the fifth note. In the chromatic form each step is a semitone | Crucifixus (measured): 21 percent of the bass moves are semitones, 70 percent are repeated notes | Crucifixus; the bass of "Erbarme dich" goes down from B to E by scale steps | wp-lament-bass; uma-edition | R |
| Chromatic fourth (passus duriusculus) | Baroque | A line that fills a fourth with semitones. The name means a hard passage |  | The bass of "Buß und Reu": F-sharp, E-sharp, E, D, C-sharp | wp-chromatic-fourth; commons-incipits | R |
| Pedal note | Baroque | The bass stays on one note while the harmony moves above it | Longest pedal notes of the corpus (measured): 48 quarter notes (St John Passion, movement 1), 13 ("O Mensch, bewein"), 9 ("Wir setzen uns") | The first bars of the opening choruses of the two Passions | uma-edition | M |
| Two groups in dialogue | Baroque | Two choirs answer each other with short calls and questions |  | St Matthew Passion, movement 1 ("Sehet!" - "Wen?") | wp-smp | R |
| Solo instrument as a second voice | Baroque | In an aria, the instrument and the voice have the same material and answer each other | Violin: 2.2 notes for each quarter note; alto: 0.9 (measured) | "Erbarme dich" | wp-smp; uma-edition | R |
| Halo | Baroque | Long soft chords of the strings around the words of one person |  | The words of Jesus in the St Matthew Passion | wp-smp | R |
| Picture in the instruments | Baroque | A figure of the instruments shows one word of the text: drops, blows, trembling |  | Flutes in "Buß und Reu"; strings in "Erbarm es Gott"; bass in "O Schmerz" | wp-smp; commons-incipits | R |
| Melody voice and triad voice (tintinnabuli) | Since 1976 | One voice moves by step. A second voice has only the notes of one triad. "The melody and the accompaniment is one" | The triad voice takes the nearest note of the triad above or below the melody note | Pärt, Für Alina; Passio | wp-tintinnabuli; wp-passio | R |
| Rhythm from the text | Since 1982 | The note values come from the words. A syllable is short, medium, or long: the punctuation and the position in the phrase decide | Last word before a full stop: each syllable long. Stressed syllable of the last word before a comma: medium. All other syllables: short | Pärt, Passio | wp-passio | R |
| A pitch centre for each person | Since 1982 | Each person of the story has a note value and a pitch centre. Christ has the longest and lowest notes | Fifths in a chain: D, A, E, B. The centre of Christ is E | Pärt, Passio | wp-passio | R |
| Canon in different speeds | Old and new | All voices have the same line, but each voice has its own note value (a prolation canon or mensuration canon) | A canon "by augmentation" has the note values doubled | Pärt, Cantus in Memoriam Benjamin Britten (a canon on one motif in A minor) | wp-prolation; wp-cantus | R |
| One phrase in free tempos | Since 1988 | All voices sing the same chorale phrase, each in its own tempo. They wait at the end of the phrase until all are there | Three phrases of a chorale of Bach; soft start and soft end | Nystedt, Immortal Bach | wp-immortal-bach | R |
| Phase shift | Since 1965 | Two players have the same short figure. One goes a little faster: the figure moves against itself and comes back to the unison | First an echo, then each note two times, then a complex ring | Reich; in Richter's version of Vivaldi the old figures are in loops and in phase shifts | wp-phase; wp-richter | R |
| Cut and loop | Since 2012 | Take a small part of an old work. Repeat it and change its context. Remove the rest | Richter removed 75 percent of the material of Vivaldi | Richter, Recomposed: The Four Seasons | wp-richter | R |
| Theme that loses its notes | Since 1980 | Each variation removes one note from the start and one from the end of the theme. Later the theme comes back note by note, backwards | The theme of The Musical Offering; the full theme comes only at the end | Gubaidulina, Offertorium | wp-offertorium | R |
| Colour melody | Since 1909 | One line goes from instrument to instrument. The change of colour shows the motifs of the line | Gubaidulina gives the theme of Bach to different instruments, as Webern did | Webern, Ricercata; Gubaidulina, Offertorium | wp-klang; wp-offertorium | R |
| Many lines as one cloud (micropolyphony) | Since 1961 | Many voices play canons at small distances and different speeds. The ear hears a texture, not the lines | Ligeti: "you cannot actually hear the polyphony, the canon" | Ligeti, Atmosphères and Lontano | wp-micropolyphony | R |
| Two styles at the same time | Since 1968 | Old tonal music and new music sound together or one after the other |  | Pärt, Credo; Schnittke, Concerto Grosso No. 1 | wp-credo; wp-schnittke-cg1; wp-polystylism | R |
| The chorale in a foreign language | Since 1935 | A chorale of Bach comes into music with a different harmony. The plain chords are an event | Berg: the row has triads, and the last section is a set of chorale variations. Penderecki: a major triad comes only two times | Berg, Violin Concerto; Penderecki, St Luke Passion | wp-berg-vc; wp-penderecki-luke | R |
| The old form with new content | Since 1985 | Keep the form of a Passion of Bach (story, response, chorale) and put a different story or a different musical language into it | Lang: 15 numbers; story numbers and response numbers in turn; the titles of the response numbers come from the text of Picander | Lang, the little match girl passion; Kagel, Sankt-Bach-Passion | lang-note; wp-kagel | R |
| The quotation that waits | Since 2009 | The music has the harmony of the old piece from the start, but not its form. The quotation comes late and is short | Shaw: "modular sequences strung together out of context"; the chorale can be recognised at about the middle | Shaw, Punctum | bso-punctum | R |
| One melody shared by two players (hocket) | Old and new | Two voices have the notes of one melody in turns: one sounds while the other rests |  | Medieval music; used again in the 20th century | wp-hocket | R |
| One line in more than one form (heterophony) | Old and new | Players have the same melody at the same time, each with a different rhythm or with ornaments |  | Usual in many traditions outside Europe | wp-heterophony | R |
| Rhythm cycle and pitch cycle of different lengths | Old and new | A rhythm pattern repeats in one voice. The pitches repeat in a cycle of a different length (isorhythm) | The pattern of the rhythm is the talea; the pattern of the pitches is the color | Motets of the 14th century; used again in the 20th century | wp-isorhythm | R |
| Fall with no end | Since 1964 | A sound seems to go down for ever: when a line goes out at the bottom, the same line comes in at the top | A sound of sine waves at octaves | The Shepard scale; the same idea is possible with the entries of a canon | wp-shepard | R |

Data file: [`research/tables/devices.csv`](../research/tables/devices.csv)

### S8. Figures of musical speech

The names are those of the German theory of the 17th and 18th centuries.

| Figure | Content | Example in the passion | Use in this work | Source | Evidence |
| --- | --- | --- | --- | --- | --- |
| Music as speech (musica poetica) | German theory of the 16th and 17th centuries made the composition of music similar to the composition of a speech. Music of that time was primarily vocal music | The full work | Each musical idea of the voice comes from a word or a sentence of the text | wp-musica-poetica | R |
| Affect | Baroque theory: a piece of art gives the listener one specific emotion | Each aria has one affect and one group of instruments | One affect and one group of instruments for each number | wp-affections | R |
| Hard passage (passus duriusculus) | A line that goes by semitones through a fourth | The bass of "Buß und Reu" | The lament lines of the bass; the falls at the death scene | wp-chromatic-fourth; commons-incipits | R |
| Hard leap (saltus duriusculus) | A leap of a diminished or augmented interval, or of a seventh | The subject of "Laß ihn kreuzigen": a diminished fourth and a tritone | The music of the crowd | reference; commons-incipits | R, K |
| Call (exclamatio) | A leap up, usually of a sixth, on a call or a prayer | "Erbarme dich": the first interval is a minor sixth up. "Erbarm es Gott": a minor seventh up | The first interval of the alto in the numbers of prayer | reference; uma-edition; commons-incipits | R, K |
| Sigh (suspiratio) | Short rests cut a line into small groups; pairs of notes go down by step | The flutes of "O Mensch, bewein": pairs of sixteenth notes with a slur | The winds in the numbers of grief | reference; uma-edition | R, K |
| Fall and climb (catabasis and anabasis) | A line goes down for words of death and humility, and up for words of heaven and rising | The bass of "Erbarme dich" goes down a fifth by step | Long falls in the bass; the keys of the chorale go down | reference; uma-edition | R, K |
| Circle (circulatio) | A line turns around one note | "Können Tränen": the alto turns around G | The turn figures of the alto | reference; uma-edition | R, K |
| Run (tirata) | A fast run through a scale | The continuo at "der Vorhang im Tempel zerriß": runs of thirty-second notes | The earthquake | reference; commons-incipits | R, K |
| Trembling (bow tremolo) | One note repeats fast and softly | The bass of "O Schmerz": sixteen equal notes in a bar | Gethsemane; the darkness | reference; commons-incipits | R, K |
| All voices together (noema) | A passage where all voices have the same rhythm, in a work with much counterpoint: the words become clear | "Wahrlich, dieser ist Gottes Sohn gewesen" | The centurion's words; the plain chorales | reference; uma-edition | R, K |
| Sudden silence (aposiopesis) | A rest in all voices | After the death of Jesus, before the chorale | One long silence in the work, after the death | reference | K |
| The cross in the notes | Four notes whose outer pair and inner pair cross when lines join them, for example B-flat, A, C, B (the name BACH) | The subject of "Laß ihn kreuzigen" has this shape | The crowd; one hidden use of the four notes of the name | wp-bach-motif; commons-incipits | R |
| Sharp sign as a cross | In German the sharp sign has the name "Kreuz" (cross). Keys with many sharps can show the cross | "Laß ihn kreuzigen" ends in B major and in C-sharp major | The key plan: sharps on the way to the cross, flats at the death and the tomb | reference; wp-smp-structure | R, K |

Data file: [`research/tables/rhetoric.csv`](../research/tables/rhetoric.csv)

### S9. Performance practice

| Topic | Content | Value for this work | Source | Evidence |
| --- | --- | --- | --- | --- |
| Period instruments | Historically informed performance uses the instruments and the manner of playing of the time of the work. Period instruments have a different timbre and temperament from modern instruments | The work is for period instruments. The audio uses samples of modern instruments: each difference is in the audio document | wp-hip | R |
| Pitch | Baroque orchestras of today usually play at a' = 415 Hz, about one semitone below the modern pitch | The score is in the written keys. The audio is one semitone lower than a' = 440 Hz | reference | K |
| Size of the string group | The orchestras of Bach were small: two or three players for each violin part | 4 first violins, 4 second violins, 3 violas, 2 violoncellos, 1 violone | reference | K |
| Recitative | In simple recitative the singer has the rhythm of speech, and each syllable usually has one note. The continuo plays short chords | The story numbers of the alto. The rhythm follows the German words | wp-recitative | R |
| Recitative with instruments | The instruments have one fixed figure or long chords. The voice is more melodic than in simple recitative | The numbers before the arias; the words of Jesus | wp-smp; wp-vox-christi | R |
| Continuo | A bass line with figures. A keyboard instrument or a lute makes the chords; bass instruments play the line | The score gives the bass line with figures and a written part for each chord instrument | wp-figured-bass | R |
| Da capo aria | The usual form of a baroque aria: a first part, a second part, and the first part again | Not used in its full form: a return is always changed and shorter | wp-smp; reference | R, K |
| Ornaments | The voice and the solo instruments add appoggiaturas, trills, and slides. Many are written in the sources as small notes | Written in the score as small notes and trill signs | uma-edition | R |
| Voice of the alto | A contralto or a countertenor can sing an alto part of the baroque period | One singer: a mezzo-soprano or a countertenor | wp-nisi; wp-alto | R |
| Siciliano | A slow movement in 6/8 or 12/8 with lilting rhythms, usually in a minor key; it has a pastoral mood and frequently dotted rhythms | The metre of the opening and of the number of mercy | wp-siciliana | R |

Data file: [`research/tables/practice.csv`](../research/tables/practice.csv)

## Part 3: Style profiles

A style profile is a set of target ranges for the new work. Each range has a low value and a high value. The study team set each range around a measured value or a sourced value. The column "Basis" gives that value.

### P1. Profile "All": the full work

| Group | Parameter | Low | High | Unit | Basis | Code |
| --- | --- | --- | --- | --- | --- | --- |
| Form | Number of numbers | 12 | 16 | numbers | Lang: 15 numbers in 35 minutes. Bach: 68 movements in about 165 minutes. BWV 170: 5 movements in 24 minutes | R |
| Form | Length of an aria number | 3 | 6.5 | minutes | The five arias of the Passion in the corpus have 4.1 to 6.4 minutes at the tempo of the edition | M |
| Form | Position of the death of Jesus | 0.70 | 0.85 | share of the duration | Lang: number 11 of 15 (0.73 by number). Bach: movement 61 of 68 (0.90 by number) | R |
| Form | Layers of text | 3 | 3 | layers | Bach: Gospel text, poems, chorales. Lang keeps story numbers and response numbers in turn | R |
| Harmony | Different pitch classes in one bar | 6.5 | 8.5 | pitch classes | The 14 movements of the corpus have 5.6 to 9.0 (middle value 7.3); the plain chorales have 7.0 in four quarter notes | M |
| Harmony | Notes outside the scale of the number | 0.03 | 0.12 | share of the note time | The 14 movements have 0.03 to 0.12; the chorales have 0.03 (middle value) | M |
| Harmony | Chords built from thirds | 0.60 | 0.90 | share of the chord time | The 14 movements have 0.49 to 0.89; the chorales have 0.88 (middle value) | M |
| Texture | Lines that sound at the same time in a number for the voice | 2 | 5.5 | lines | The arias of the corpus have 2.0 to 5.2 lines (middle value 4.3) | M |
| Texture | Lines that sound at the same time in a number for the full orchestra | 6.5 | 10.5 | lines | The choruses of the corpus have 6.6 to 10.5 lines | M |

### P2. Profile "Voice": the alto

| Group | Parameter | Low | High | Unit | Basis | Code |
| --- | --- | --- | --- | --- | --- | --- |
| Range | Lowest note | A3 | B3 | pitch | Alto lines of the corpus: A3 ("Et misericordia"), B3 ("Erbarme dich"), C4 ("Können Tränen") | M |
| Range | Highest note | D5 | E5 | pitch | Alto lines of the corpus: C-sharp 5, E-flat 5, E5. F5 is possible one time at the highest point of the work | M |
| Range | Middle of the voice (the median pitch) | F-sharp 4 | A4 | pitch | Alto lines of the corpus: F-sharp 4, A4, A4 | M |
| Range | Zone of 90 percent of the time | C-sharp 4 | D5 | pitch | Alto lines of the corpus: the 5th percentile is C-sharp 4 to E-flat 4, the 95th percentile is B4 to D5 | M |
| Line | Moves by step (semitone or whole tone) | 0.70 | 0.76 | share of the moves | Alto lines of the corpus: 0.72, 0.73, 0.75 | M |
| Line | Moves by semitone | 0.34 | 0.38 | share of the moves | Alto lines of the corpus: 0.34, 0.37, 0.38 | M |
| Line | Moves by a third | 0.05 | 0.15 | share of the moves | Alto lines of the corpus: 0.05, 0.10, 0.14 | M |
| Line | Moves by a sixth or more | 0.02 | 0.06 | share of the moves | Alto lines of the corpus: 0.02, 0.05, 0.06. These are the calls and the cries | M |
| Line | Notes for each quarter note in an aria | 0.8 | 1.25 | notes | Alto lines of the corpus: 0.82, 0.94, 1.23 | M |
| Time | Share of an aria in which the voice sings | 0.50 | 0.60 | share of the duration | Alto lines of the corpus: 0.50, 0.55, 0.60. The instruments have the other time | M |

### P3. Profile "Solo instrument": the partner of the voice in an aria

| Group | Parameter | Low | High | Unit | Basis | Code |
| --- | --- | --- | --- | --- | --- | --- |
| Line | Notes for each quarter note | 1.7 | 2.5 | notes | Solo violin of "Erbarme dich": 2.2. Flute of "Aus Liebe": 2.5. Flute of BWV 198: 1.9 | M |
| Line | Notes of a sixteenth or shorter | 0.60 | 0.85 | share of the notes | Solo violin: 0.62. Flutes: 0.66 and 0.85 | M |

### P4. Profile "Bass": the continuo line

| Group | Parameter | Low | High | Unit | Basis | Code |
| --- | --- | --- | --- | --- | --- | --- |
| Line | Notes for each quarter note in an aria | 0.75 | 1.7 | notes | Continuo lines of the arias of the corpus: 0.75 to 1.66 | M |
| Line | Moves by semitone | 0.07 | 0.31 | share of the moves | Continuo lines of the corpus: 0.05 to 0.31; the chorale basses have 0.26 (middle value) | M |
| Line | Repeated notes in a number with a pulse bass | 0.55 | 0.75 | share of the moves | "Erbarme dich": 0.59. Crucifixus: 0.70. St John Passion, movement 1: 0.71 | M |
| Line | Longest pedal note | 9 | 48 | quarter notes | "Wir setzen uns": 9. "O Mensch, bewein": 13. St John Passion, movement 1: 48 | M |

### P5. Profile "Aria": a number for the voice with instruments

| Group | Parameter | Low | High | Unit | Basis | Code |
| --- | --- | --- | --- | --- | --- | --- |
| Harmony | Chords with a semitone clash | 0.13 | 0.28 | share of the chord time | The arias of the corpus have 0.13 to 0.28 | M |
| Harmony | Major and minor triads | 0.20 | 0.35 | share of the sounding time | The arias of the corpus with three or more lines have 0.21 to 0.35 | M |

### P6. Profile "Chorus": a number for the full orchestra

| Group | Parameter | Low | High | Unit | Basis | Code |
| --- | --- | --- | --- | --- | --- | --- |
| Harmony | Chords with a semitone clash | 0.15 | 0.58 | share of the chord time | The choruses of the corpus have 0.15 to 0.58. The highest values are in the opening chorus of the St John Passion and in "Qui tollis" | M |

### P7. Profile "Chorale": a chorale setting

| Group | Parameter | Low | High | Unit | Basis | Code |
| --- | --- | --- | --- | --- | --- | --- |
| Form | Length of a setting | 44 | 64 | quarter notes | The 11 settings of the Passion in the edition of the chorales | M |
| Form | Phrases | 4 | 8 | phrases | The 11 settings of the Passion | M |
| Harmony | Major and minor triads | 0.50 | 0.63 | share of the sounding time | The 11 settings of the Passion. All 370 chorales: 0.61 (middle value) | M |
| Harmony | Chords with a semitone clash | 0.03 | 0.16 | share of the chord time | The 11 settings of the Passion. All 370 chorales: 0.07 (middle value) | M |
| Harmony | Notes outside the scale | 0.026 | 0.063 | share of the note time | The 11 settings of the Passion. All 370 chorales: 0.029 (middle value) | M |
| Line | Semitone moves of the bass | 0.16 | 0.40 | share of the moves | The 11 settings of the Passion. The last setting of the Passion chorale has 0.375 | M |
| Line | Note starts off the beat for each quarter note | 0.58 | 1.09 | note starts | The 11 settings of the Passion: the passing notes of the lower voices | M |

Data file: [`research/tables/profiles.csv`](../research/tables/profiles.csv)

## Limits of the study

- The measured movements are MIDI files of a modern edition. The tempo and the duration of each file are a decision of the editor.
- The study measured 7 of the 68 movements of the Passion as full movements. No open data were found for the Gospel recitatives; the study read only their first bars.
- The edition of the chorales gives some settings in a key that is not the key of the Passion.
- A MIDI file does not have the spelling of the notes. The count of "notes outside the scale" uses one scale for a full movement: a passage in a different key adds to the count.
- The study of the later works uses encyclopedia articles and the notes of the composers. The study team did not examine their scores: they are not free.
- The study did not use the books on the Passion (Dürr, Platen, Chafe, Melamed, Wolff). A later edition of the study can add them.
- One archive of free scores (the Choral Public Domain Library) has the full Passion as MusicXML files. The archive does not permit automatic downloads: the study did not use these files.
- The study has no measured values of recordings yet. The audio stage needs them (loudness, tone balance, tempo).

## Sources

| Key | Source | Access |
| --- | --- | --- |
| `reference` | Standard reference knowledge of music theory and music history. The study team did not read a source for the rows with this key. | not read |
| `wp-smp` | Wikipedia. "St Matthew Passion". History, versions, text, composition, compositional style, reception. <https://en.wikipedia.org/wiki/St_Matthew_Passion> | read |
| `wp-smp-structure` | Wikipedia. "St Matthew Passion structure". Scenes, and one table row for each movement: voices, key, time signature, instruments, first words, source of the text. <https://en.wikipedia.org/wiki/St_Matthew_Passion_structure> | read |
| `bischof-244` | Bischof, Walter F. "BWV 244 Matthäuspassion". The German text and the scoring of each movement. University of Alberta. <https://webdocs.cs.ualberta.ca/~wfb/cantatas/244.html> | read |
| `commons-incipits` | Wikimedia Commons, category "BWV 244 Incipit". The first bars of the movements of BWV 244 as images, with the LilyPond text of 67 of them. By the user Wikiwal, 2011. <https://commons.wikimedia.org/wiki/Category:BWV_244_Incipit> | read |
| `uma-edition` | Alvarez, Nancho (editor). Scores of movements of J. S. Bach (BWV 198, 232, 243, 244, 245) with their LilyPond text and MIDI files. No licence statement. <https://www.victoria.uma.es/varios/> | read and measured |
| `sapp-chorales` | Sapp, Craig Stuart. A digital edition of 370 J. S. Bach chorales in the Humdrum format, after the edition of Breitkopf & Härtel (about 1875). CC BY-NC-SA 4.0. <https://github.com/craigsapp/bach-370-chorales> | measured |
| `lang-note` | Lang, David. Program note and text of "the little match girl passion" (2007). <https://davidlangmusic.com/music/little-match-girl-passion> | read |
| `wp-lmgp` | Wikipedia. "The Little Match Girl Passion". <https://en.wikipedia.org/wiki/The_Little_Match_Girl_Passion> | read |
| `wp-passio` | Wikipedia. "Passio (Pärt)". Forces, structure, and the rules for the note values. <https://en.wikipedia.org/wiki/Passio_(P%C3%A4rt)> | read |
| `wp-tintinnabuli` | Wikipedia. "Tintinnabuli". <https://en.wikipedia.org/wiki/Tintinnabuli> | read |
| `wp-cantus` | Wikipedia. "Cantus in Memoriam Benjamin Britten". <https://en.wikipedia.org/wiki/Cantus_in_Memoriam_Benjamin_Britten> | read the introduction |
| `wp-fratres` | Wikipedia. "Fratres". <https://en.wikipedia.org/wiki/Fratres> | read the introduction |
| `wp-credo` | Wikipedia. "Credo (Pärt)". <https://en.wikipedia.org/wiki/Credo_(P%C3%A4rt)> | read the introduction |
| `wp-immortal-bach` | Wikipedia. "Immortal Bach". <https://en.wikipedia.org/wiki/Immortal_Bach> | read |
| `wp-offertorium` | Wikipedia. "Offertorium (Gubaidulina)". <https://en.wikipedia.org/wiki/Offertorium_(Gubaidulina)> | read |
| `wp-berg-vc` | Wikipedia. "Violin Concerto (Berg)". <https://en.wikipedia.org/wiki/Violin_Concerto_(Berg)> | read the first half |
| `wp-richter` | Wikipedia. "Recomposed by Max Richter: Vivaldi – The Four Seasons". <https://en.wikipedia.org/wiki/Recomposed_by_Max_Richter:_Vivaldi_%E2%80%93_The_Four_Seasons> | read |
| `wp-pulcinella` | Wikipedia. "Pulcinella (ballet)". <https://en.wikipedia.org/wiki/Pulcinella_(ballet)> | read the introduction |
| `wp-schnittke-cg1` | Wikipedia. "Concerto Grosso No. 1 (Schnittke)". <https://en.wikipedia.org/wiki/Concerto_Grosso_No._1_(Schnittke)> | read the introduction |
| `wp-proverb` | Wikipedia. "Proverb (Reich)". <https://en.wikipedia.org/wiki/Proverb_(Reich)> | read the introduction |
| `wp-penderecki-luke` | Wikipedia. "St Luke Passion (Penderecki)". <https://en.wikipedia.org/wiki/St_Luke_Passion_(Penderecki)> | read the introduction |
| `wp-golijov` | Wikipedia. "La Pasión según San Marcos". <https://en.wikipedia.org/wiki/La_Pasi%C3%B3n_seg%C3%BAn_San_Marcos> | read the introduction |
| `wp-kagel` | Wikipedia. "Sankt-Bach-Passion". <https://en.wikipedia.org/wiki/Sankt-Bach-Passion> | read the introduction |
| `wp-gubaidulina-jp` | Wikipedia. "Johannes-Passion (Gubaidulina)". <https://en.wikipedia.org/wiki/Johannes-Passion_(Gubaidulina)> | read the introduction |
| `wp-vivaldi-stabat` | Wikipedia. "Stabat Mater (Vivaldi)". <https://en.wikipedia.org/wiki/Stabat_Mater_(Vivaldi)> | read |
| `wp-nisi` | Wikipedia. "Nisi Dominus (Vivaldi)". <https://en.wikipedia.org/wiki/Nisi_Dominus_(Vivaldi)> | read the introduction |
| `wp-pergolesi` | Wikipedia. "Stabat Mater (Pergolesi)". <https://en.wikipedia.org/wiki/Stabat_Mater_(Pergolesi)> | read the introduction |
| `wp-bwv170` | Wikipedia. "Vergnügte Ruh, beliebte Seelenlust, BWV 170". <https://en.wikipedia.org/wiki/Vergn%C3%BCgte_Ruh> | _beliebte_Seelenlust |
| `wp-bwv54` | Wikipedia. "Widerstehe doch der Sünde, BWV 54". <https://en.wikipedia.org/wiki/Widerstehe_doch_der_S%C3%BCnde> | _BWV_54 |
| `wp-bwv82` | Wikipedia. "Ich habe genug, BWV 82". <https://en.wikipedia.org/wiki/Ich_habe_genug> | _BWV_82 |
| `wp-bwv1083` | Wikipedia. "Tilge, Höchster, meine Sünden, BWV 1083". <https://en.wikipedia.org/wiki/Tilge> | _H%C3%B6chster |
| `wp-bwv198` | Wikipedia. "Laß, Fürstin, laß noch einen Strahl, BWV 198". <https://en.wikipedia.org/wiki/La%C3%9F> | _F%C3%BCrstin |
| `wp-bwv769` | Wikipedia. "Canonic Variations on 'Vom Himmel hoch da komm' ich her'". <https://en.wikipedia.org/wiki/Canonic_Variations_on_%22Vom_Himmel_hoch_da_komm%27_ich_her%22> | read the introduction |
| `wp-musical-offering` | Wikipedia. "The Musical Offering". <https://en.wikipedia.org/wiki/The_Musical_Offering> | read the introduction |
| `wp-via-crucis` | Wikipedia. "Via crucis (Liszt)". <https://en.wikipedia.org/wiki/Via_crucis_(Liszt)> | read the introduction |
| `wp-partita` | Wikipedia. "Partita for 8 Voices". <https://en.wikipedia.org/wiki/Partita_for_8_Voices> | read the introduction |
| `bso-punctum` | Boston Symphony Orchestra. Program note on Caroline Shaw, "Punctum", with the words of the composer. <https://www.bso.org/works/punctum> | read |
| `pbo-shaw` | Philharmonia Baroque Orchestra & Chorale. Press release on the recording of Caroline Shaw, "Is a Rose" and "The Listeners" (2020). <https://philharmonia.org/press-release-shaw-cd/> | read |
| `wp-lament-bass` | Wikipedia. "Lament bass". <https://en.wikipedia.org/wiki/Lament_bass> | read the introduction |
| `wp-chromatic-fourth` | Wikipedia. "Chromatic fourth" (passus duriusculus). <https://en.wikipedia.org/wiki/Chromatic_fourth> | read the introduction |
| `wp-musica-poetica` | Wikipedia. "Musica poetica". <https://en.wikipedia.org/wiki/Musica_poetica> | read the introduction |
| `wp-affections` | Wikipedia. "Doctrine of the affections". <https://en.wikipedia.org/wiki/Doctrine_of_the_affections> | read the introduction |
| `wp-micropolyphony` | Wikipedia. "Micropolyphony". <https://en.wikipedia.org/wiki/Micropolyphony> | read the introduction |
| `wp-prolation` | Wikipedia. "Prolation canon". <https://en.wikipedia.org/wiki/Prolation_canon> | read the introduction |
| `wp-phase` | Wikipedia. "Phase music". <https://en.wikipedia.org/wiki/Phase_music> | read the introduction |
| `wp-polystylism` | Wikipedia. "Polystylism". <https://en.wikipedia.org/wiki/Polystylism> | read the introduction |
| `wp-klang` | Wikipedia. "Klangfarbenmelodie". <https://en.wikipedia.org/wiki/Klangfarbenmelodie> | read the introduction |
| `wp-shepard` | Wikipedia. "Shepard tone". <https://en.wikipedia.org/wiki/Shepard_tone> | read the introduction |
| `wp-hocket` | Wikipedia. "Hocket". <https://en.wikipedia.org/wiki/Hocket> | read the introduction |
| `wp-heterophony` | Wikipedia. "Heterophony". <https://en.wikipedia.org/wiki/Heterophony> | read the introduction |
| `wp-isorhythm` | Wikipedia. "Isorhythm". <https://en.wikipedia.org/wiki/Isorhythm> | read the introduction |
| `wp-stretto` | Wikipedia. "Stretto". <https://en.wikipedia.org/wiki/Stretto> | read the introduction |
| `wp-passacaglia` | Wikipedia. "Passacaglia". <https://en.wikipedia.org/wiki/Passacaglia> | read the introduction |
| `wp-oboe-da-caccia` | Wikipedia. "Oboe da caccia". <https://en.wikipedia.org/wiki/Oboe_da_caccia> | read the introduction |
| `wp-oboe-damore` | Wikipedia. "Oboe d'amore". <https://en.wikipedia.org/wiki/Oboe_d%27amore> | read the introduction |
| `wp-viol` | Wikipedia. "Viol". <https://en.wikipedia.org/wiki/Viol> | read the introduction |
| `wp-theorbo` | Wikipedia. "Theorbo". <https://en.wikipedia.org/wiki/Theorbo> | read the introduction |
| `wp-violone` | Wikipedia. "Violone". <https://en.wikipedia.org/wiki/Violone> | read the introduction |
| `wp-countertenor` | Wikipedia. "Countertenor". <https://en.wikipedia.org/wiki/Countertenor> | read the introduction |
| `wp-alto` | Wikipedia. "Alto". <https://en.wikipedia.org/wiki/Alto> | read the introduction |
| `wp-evangelist` | Wikipedia. "Evangelist (Bach)". <https://en.wikipedia.org/wiki/Evangelist_(Bach)> | read the introduction |
| `wp-vox-christi` | Wikipedia. "Vox Christi". <https://en.wikipedia.org/wiki/Vox_Christi> | read the introduction |
| `wp-chorale-fantasia` | Wikipedia. "Chorale fantasia". <https://en.wikipedia.org/wiki/Chorale_fantasia> | read the introduction |
| `wp-siciliana` | Wikipedia. "Siciliana". <https://en.wikipedia.org/wiki/Siciliana> | read the introduction |
| `wp-recitative` | Wikipedia. "Recitative". <https://en.wikipedia.org/wiki/Recitative> | read the introduction |
| `wp-figured-bass` | Wikipedia. "Figured bass". <https://en.wikipedia.org/wiki/Figured_bass> | read the introduction |
| `wp-hip` | Wikipedia. "Historically informed performance". <https://en.wikipedia.org/wiki/Historically_informed_performance> | read the introduction |
| `wp-bach-motif` | Wikipedia. "BACH motif". <https://en.wikipedia.org/wiki/BACH_motif> | read the introduction |
| `wp-o-lamm` | Wikipedia. "O Lamm Gottes, unschuldig". <https://en.wikipedia.org/wiki/O_Lamm_Gottes> | _unschuldig |
| `wp-herzliebster` | Wikipedia. "Herzliebster Jesu". <https://en.wikipedia.org/wiki/Herzliebster_Jesu> | read the introduction |
