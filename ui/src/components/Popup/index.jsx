import React from 'react';
import './index.css';

const Popup = ({ handleClose, show }) => {
	const showHideClassName = show ? "popup display-block" : "popup display-none";
	
	return(
		<div className={showHideClassName}>
			<section className="popup-main">
				<h2>This is a popup</h2>
				<p>Some content for the popup</p>
				<button onClick={handleClose}>Close</button>
			</section>
		</div>
	);
};

export default index;
