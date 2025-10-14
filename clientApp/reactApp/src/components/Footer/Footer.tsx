import { Link } from "react-router-dom";
import styles from "./Footer.module.css";

const Footer = () => {
  return (
    <footer className={styles.footer}>
      <nav className={styles.links} aria-label="קישורים לרשתות חברתיות">
        <span className={styles.name}>Or Israeli@</span>

        <a
          className={styles.link}
          href="mailto:someone@example.com"
          target="_blank"
        >
          or.p.israeli@gmail.com
        </a>
        <a
          className={styles.link}
          href="https://github.com/Enterisr"
          target="_blank"
          rel="noopener noreferrer"
        >
          GitHub
        </a>
        <a
          className={styles.link}
          href="https://www.linkedin.com/in/or-israeli-483497170/"
          target="_blank"
          rel="noopener noreferrer"
        >
          LinkedIn
        </a>
        <Link to="/disclaimer" className={styles.link}>
          הצהרת אחריות
        </Link>
      </nav>
      <div className={styles.kastach}>
        המערכת בהרצה, ועל כן ייתכנו שגיאות, אי דיוקים, פרוטוקולים חסרים וכאוס
        כללי
      </div>
    </footer>
  );
};

export default Footer;
