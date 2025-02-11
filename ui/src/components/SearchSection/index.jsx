// import Input from "../../components/imagec/Input";
// import Img from "../../components/imagec/Img";
// import React from "react";


// export default function SearchSection() {
//     const [searchvalue, setSearchValue] = React.useState("");

//     return (
//     <>
//     <div className="flex flex-col items-center bg-gray-300 p-5">
//       <div className="container-xs mb-3 flex-col gap-9 md:px-5">
//         <div className="flex flex-col items-start px-1">
//             <Input
//             name="search"
//             placeholder="Search anything..."
//             value={searchvalue}
//             onChange={(e) => setSearchValue(e.target.value)}
//             prefix={
//                 <Img src="images/img_wpfsearch.svg" alt="Wpf:search" className="w-[26px] h-[26px] object-contain" />
//             }
//             // suffix={
//             //     searchvalue?.length > 0 ? (
//             //         <CloseSvg onClick={() => setSearchValue("")} height={26} width={26} fillcolor="#000000ff" />
//             //     ) : null
//             // }
//             className="rounded-[14-px] text-[12.16px] pl-[18px] mt-[-2px] h-[44px] w-[22%] relative flex items-center gap-3 self-center border border-solid border-black-900 pr-3 text-gray-800"
//             /> 
//         </div>
//       </div>
//       </div>
//     </>
//   );
// }

import React from "react";
import search from "./search.png";

const SearchBox = () => {
  return (
    <div className="absolute w-[375px] h-[44px] left-[900px] top-[100px] bg-white border border-[#594F4F] rounded-md flex items-center px-4">
      {/* Search Icon */}
      <img
        src={search}
        alt="Search"
        className="absolute w-[26px] h-[26px] left-[19px] top-[9px]"
      />

      {/* Input Field */}
      <input
        type="text"
        placeholder="Search anything..."
        className="absolute w-[203px] h-[44px] left-[57px] top-0 text-[#413E3E] text-[12.46px] leading-[12px] font-normal font-inter outline-none bg-transparent"
      />
    </div>
  );
};

export default SearchBox;


