import { Routes, Route } from "react-router-dom";
import Home from "../../pages/Home/Home";
import MKPage from "../../pages/MKPage/MKPage";

const AppRouter = () => {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/search/:query" element={<Home />} />
      <Route path="/mk/:mkName/:query" element={<MKPage />} />
    </Routes>
  );
};

export default AppRouter;
