# אימון מסווג חשיבות אמירות

מדריך זה מסביר איך להשתמש בסקריפטים לאימון מסווג שיקבע אם אמירה בכנסת חשובה או לא.

## קבצים

1. **`simple_trainer.py`** - גרסה פשוטה המבוססת על הקוד שנתת
2. **`labels_trainer.py`** - גרסה מתקדמת יותר עם יכולות נוספות

## איך להשתמש - גרסה פשוטה

### שלב 1: יצירת קבצי אימון

```bash
cd training
python simple_trainer.py --create
```

זה יוצר:
- `embeddings.npy` - וקטורי האמירות
- `sentences.npy` - טקסט האמירות  
- `labels.npy` - תוויות (ריק בהתחלה)
- `labels_to_fill.csv` - קובץ CSV לתיוג ידני

### שלב 2: תיוג האמירות

פתח את הקובץ `labels_to_fill.csv` ומלא את העמודה `label`:
- `1` = אמירה חשובה
- `0` = אמירה לא חשובה

**טיפים לתיוג:**
- אמירות קצרות כמו "מי בעד? מי נגד?" בדרך כלל לא חשובות
- אמירות עם מספרים, תקציבים, חקיקה - בדרך כלל חשובות
- אמירות ארוכות עם תוכן מהותי - בדרך כלל חשובות

### שלב 3: עדכון התוויות

```bash
python simple_trainer.py --update-labels
```

זה יעתיק את התוויות מה-CSV לקובץ NPY.

### שלב 4: אימון המודל

```bash
python simple_trainer.py --train
```

זה יאמן מסווג לוגיסטי וישמור אותו ב-`classifier.pkl`.

## איך להשתמש - גרסה מתקדמת

### יצירת קובץ תיוג

```bash
python labels_trainer.py --create-labels --samples 500
```

### אימון

```bash
python labels_trainer.py --train --threshold 0.8
```

## המודל

המודל משתמש ב:

1. **Sentence embeddings** - וקטורים של האמירות מהמודל הקיים
2. **Features ידניים:**
   - יש מספרים בטקסט
   - יש אזכור כסף/תקציב
   - שפה פרוצדורלית ("מי בעד", "תודה" וכו')
   - שאלות (?)
   - אורך הטקסט
   - מילים רגשיות חזקות
   - אזכור חקיקה/מדיניות

## קבצי פלט

- `classifier.pkl` - המודל המאומן
- `feature_scaler.pkl` - סקיילר לנורמליזציה
- `threshold_analysis.png` - גרף ניתוח threshold
- `importance_labels.csv` - קובץ התיוג (גרסה מתקדמת)

## שימוש במודל המאומן

```python
from training.labels_trainer import ImportanceTrainer

trainer = ImportanceTrainer()
trainer.load_model()

# לחזות חשיבות של טקסטים חדשים
# (צריך embeddings של הטקסטים)
probabilities = trainer.predict_importance(texts, embeddings)
```

## דגשים

- התיוג הידני הוא השלב הכי חשוב - איכות התוויות קובעת את איכות המודל
- מומלץ לתייג לפחות 500-1000 דוגמאות
- שמור על איזון בין דוגמאות חשובות ולא חשובות (בערך 50-50)
- המודל משתמש ב-`class_weight='balanced'` כדי להתמודד עם חוסר איזון

## פרמטרים למודל

- `threshold=0.8` - סף להחלטה (ברירת מחדל 0.8)
- `test_size=0.2` - גודל סט הולידציה
- `max_iter=2000` - מקסימום איטרציות לאימון
- `class_weight='balanced'` - איזון אוטומטי של המחלקות