// import DrawingCanvas from "../components/Canvas/DrawingCanvas";
// import BalloonSidebar from "../components/Sidebar/BalloonSidebar";
// import TopToolbar from "../components/Toolbar/TopToolbar";

// const ViewerPage = () => {
//   return (
//     <div className="h-screen flex flex-col bg-gray-900 text-white">
//       <TopToolbar />

//       <div className="flex flex-1 overflow-hidden">
//         <div className="flex-1 bg-gray-800">
//           <DrawingCanvas />
//         </div>

//         <div className="w-80 bg-gray-950 border-l border-gray-700">
//           <BalloonSidebar />
//         </div>
//       </div>
//     </div>
//   );
// };

// export default ViewerPage;

import DrawingCanvas from "../components/Canvas/DrawingCanvas";
import BalloonSidebar from "../components/Sidebar/BalloonSidebar";
import TopToolbar from "../components/Toolbar/TopToolbar";

const ViewerPage = () => {
  return (
    <div className="h-screen flex flex-col bg-gray-900 text-white">
      <TopToolbar />

      <div className="flex flex-1 min-h-0 overflow-hidden">
        <div className="flex-1 min-w-0 min-h-0 relative bg-gray-800">
          <DrawingCanvas />
        </div>

        <div className="w-80 shrink-0 min-h-0 bg-gray-950 border-l border-gray-700">
          <BalloonSidebar />
        </div>
      </div>
    </div>
  );
};

export default ViewerPage;
