import { useNavigate } from "react-router-dom";
import { useSearch } from "../../hooks/useSearch";
import logo from "../../assets/logo.png";
import "./Header.css";
function Header() {
  const navigate = useNavigate();
  const { clearResults } = useSearch();
  function navigateHome() {
    clearResults();
    navigate("");
  }
  return (
    <header className="app-header">
      <div className="logo-container" onClick={navigateHome}>
        <img src={logo} alt="App Logo" className="app-logo" />
      </div>
      <h1 onClick={navigateHome}>מידעכנסת</h1>
    </header>
  );
}

export default Header;
