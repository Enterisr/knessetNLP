import { Link } from "react-router-dom";
import styles from "./Disclaimer.module.css";

const creditedModels = [
  {
    name: "imvladikon/sentence-transformers-alephbert",
    url: "https://huggingface.co/imvladikon/sentence-transformers-alephbert",
  },
  {
    name: "classla/xlm-r-parlasent",
    url: "https://huggingface.co/classla/xlm-r-parlasent",
  },
];

const Disclaimer = () => {
  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1 className={styles.title}>הצהרת אחריות</h1>
        <p className={styles.intro}>
          האתר והמידע המוצג בו ניתנים כמות שהם (“As Is”) לצרכים לימודיים
          וניסיוניים בלבד, ופותחו על־ידי במהלך חופשת סמסטר אחת. מדובר בפרויקט
          אישי למטרות לימוד בלבד ובמימון עצמי. אין לראות בתכנים משום מקור מידע
          רשמי, ייעוץ או התחייבות מכל סוג שהוא. האתר אינו מופעל, מאושר או קשור
          בכל צורה לכנסת ישראל או לכל גורם רשמי אחר. כל הפרוטוקולים, המסמכים
          והנתונים המוצגים נאספו באופן עצמאי באמצעות ממשק ה־API הציבורי של אתר
          הכנסת. אם נעשה בשוגג שימוש לא מורשה בחומר מוגן, אנא פנו במייל ותיקון
          יבוצע בהקדם האפשרי. כרגע האתר לא מתעדכן אוטומטית.הפרוטוקולים לקוחים
          מועדות הכנסות ה-25 שהתכנסו לפני 2/10/25
        </p>
      </header>

      <section className={styles.section} aria-labelledby="models-title">
        <h2 id="models-title" className={styles.sectionTitle}>
          מודלים שהשתמשתי בהם:
        </h2>
        <ul className={styles.modelsList}>
          {creditedModels.map((model) => (
            <li key={model.name} className={styles.modelItem}>
              <a
                href={model.url}
                className={styles.modelLink}
                target="_blank"
                rel="noopener noreferrer"
              >
                {model.name}
              </a>
            </li>
          ))}
        </ul>
      </section>

      <section className={styles.section} aria-labelledby="usage-title">
        <h2 id="usage-title" className={styles.sectionTitle}>
          שימוש אחראי בממצאים
        </h2>
        <p className={styles.paragraph}>
          הפרויקט נשען על נתונים זמינים לציבור וניתוח אוטומטי באמצעות מודלים של
          עיבוד שפה טבעית. תוצאות הניתוח נועדו להעניק נקודת פתיחה נוספת לחוקרים
          ולמתעניינים בתחום, אך הן אינן מהוות תחליף לבחינה ידנית ומקצועית של
          המקורות. <br />
          <b>
            יש לך הצעה לשיפור או להמשך? המערכת עזרה? אשמח לשמוע במייל:
            <a href="r.p.israeli@gmail.com"> or.p.israeli@gmail.com</a>
          </b>
        </p>
      </section>

      <div className={styles.backLinkWrapper}>
        <Link to="/" className={styles.backLink}>
          ← חזרה לדף הבית
        </Link>
      </div>
    </div>
  );
};

export default Disclaimer;
