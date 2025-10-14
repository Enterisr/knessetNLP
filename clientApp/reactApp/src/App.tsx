import "./App.css";
import { SearchProvider } from "./contexts/SearchContext.tsx";
import AppRouter from "./components/AppRouter/AppRouter.tsx";
import Header from "./components/Header/Header.tsx";

function App() {
  return (
    <SearchProvider>
      <div className="app">
        <Header />
        <AppRouter />
      </div>
    </SearchProvider>
  );
}

export default App;
