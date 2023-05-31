import React from "react";

function Footer() {
  return (
    <footer className={"text-center p-4 bg-black mt-auto text-white"}>
      <div>
        © 2023 Copyright
        <a
          className="text-white ml-5"
          href="https://github.com/HewlettPackard/cmf"
        >
          HPE Github
        </a>
      </div>
    </footer>
  );
}

export default Footer;
