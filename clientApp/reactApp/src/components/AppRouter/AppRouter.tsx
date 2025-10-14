import { Routes, Route } from "react-router-dom";
import Home from "../../pages/Home/Home";
import MKPage from "../../pages/MKPage/MKPage";
import Disclaimer from "../../pages/Disclaimer/Disclaimer";

const AppRouter = () => {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/search/:query" element={<Home />} />
      <Route path="/mk/:mkName/:query" element={<MKPage />} />
      <Route path="/disclaimer" element={<Disclaimer />} />
    </Routes>
  );
};

export default AppRouter;
