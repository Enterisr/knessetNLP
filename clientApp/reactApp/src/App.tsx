import "./App.css";
import { SearchProvider } from "./contexts/SearchContext.tsx";
import AppRouter from "./components/AppRouter/AppRouter.tsx";
import Header from "./components/Header/Header.tsx";
import Footer from "./components/Footer/Footer.tsx";

function App() {
  return (
    <SearchProvider>
      <div className="app">
        <Header />
        <main className="app-content">
          <AppRouter />
        </main>
        <Footer />
      </div>
    </SearchProvider>
  );
}

export default App;
