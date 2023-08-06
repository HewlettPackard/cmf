// ArtifactTable.jsx
import React, { useState, useEffect } from 'react';
import './index.css';
const ArtifactTable = ({ artifacts }) => {

const [searchQuery, setSearchQuery] = useState('');
const [currentPage, setCurrentPage] = useState(1);
const [itemsPerPage] = useState(5); // Number of items to display per page
const [sortBy, setSortBy] = useState(null); // Property to sort by
const [sortOrder, setSortOrder] = useState('asc'); // Sort order ('asc' or 'desc')
const [expandedRow, setExpandedRow] = useState(null);  
const handleSearchChange = (event) => {
    setSearchQuery(event.target.value);
  };

const handlePageChange = (page) => {
    setCurrentPage(page);
  };


const handleSort = (property) => {
    if (sortBy === property) {
      // If currently sorted by the same property, toggle sort order
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      // If sorting by a new property, set it to ascending order by default
      setSortBy(property);
      setSortOrder('asc');
    }
  };

const consistentColumns = [];

const filteredData = artifacts.filter((item) =>
       (item.name && item.name.toLowerCase().includes(searchQuery.toLowerCase()))
    || (item.type && item.type.toLowerCase().includes(searchQuery.toLowerCase()))
 );

// eslint-disable-next-line
const sortedData = filteredData.sort((a, b) => {
    const aValue = a[sortBy];
    const bValue = b[sortBy];

    if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
    if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

const totalPages = Math.ceil(filteredData.length / itemsPerPage);
const indexOfLastItem = currentPage * itemsPerPage;
const indexOfFirstItem = indexOfLastItem - itemsPerPage;
const currentItems = filteredData.slice(indexOfFirstItem, indexOfLastItem);

useEffect(() => {
    setCurrentPage(1); // Reset current page to 1 when search query changes
  }, [searchQuery]);

useEffect(() => {
    setCurrentPage(1); // Reset current page to 1 when search query changes
  }, [artifacts]);


const toggleRow = (rowId) => {
    if (expandedRow === rowId) {
      setExpandedRow(null);
    } else {
      setExpandedRow(rowId);
    }
  };

// eslint-disable-next-line
const renderTableData = () => {
    if (currentItems.length === 0) {
      return (
        <tr>
          <td colSpan="4">No data available</td>
        </tr>
      );
    }

    return currentItems.map((item) => (
      <tr key={item.id}>
        {/* Render table row */}
      </tr>
    ));
  };


const renderPagination = () => {
    if (totalPages === 1){
       return null;
    }

    const totalPagesToShow = 5; // Number of pages to show in the pagination

    const startPage = Math.max(1, currentPage - Math.floor(totalPagesToShow / 2));
    const endPage = Math.min(totalPages, startPage + totalPagesToShow - 1);

    const pages = Array.from({ length: endPage - startPage + 1 }, (_, index) => startPage + index);

    return (
      <div>
        <button
          className={`pagination-button ${currentPage === 1 ? 'active' : ''}`}
          disabled={currentPage === 1}
          onClick={() => handlePageChange(currentPage - 1)}
        >
          Previous
        </button>
        {pages.map((page) => (
          <button
            key={page}
            className={`pagination-button ${currentPage === page ? 'active' : ''}`}
            onClick={() => handlePageChange(page)}
            disabled={currentPage === page}
          >
            {page}
          </button>
        ))}
        <button
          className={`pagination-button ${currentPage === totalPages ? 'active' : ''}`}
          disabled={currentPage === totalPages}
          onClick={() => handlePageChange(currentPage + 1)}
        >
          Next
        </button>

      </div>
    );
  };



return (
    <div className="container flex flex-col mx-auto p-6 mr-4">
      <div className="flex flex-col items-end m-1">
      <input
        type="text"
        value={searchQuery}
        onChange={handleSearchChange}
        placeholder="Search..."
        className="w-64 px-1 border-2 border-gray"
      />
      </div>
      <div className="overflow-x-auto">
        <div className="p-1.5 w-full inline-block align-middle">
          <table className="min-w-full divide-y divide-gray-200 border-4">
            <thead className="bg-gray-100">
              <tr className="text-xs font-bold text-left text-gray-500 uppercase">
                <th scope="col" className="id px-6 py-3"></th>
                <th scope="col" className="id px-6 py-3">id</th>
                <th scope="col" onClick={() => handleSort('name')} className="name px-6 py-3">name
                 {sortBy === 'name' && sortOrder === 'asc' && '▲'}
                 {sortBy === 'name' && sortOrder === 'desc' && '▼'}</th>
                <th scope="col" className="type px-6 py-3">Type</th>
                <th scope="col" className="url px-6 py-3">Url</th>
                <th scope="col" className="uri px-6 py-3">Uri</th>
                <th scope="col" className="git_repo px-6 py-3">Git_Repo</th>
                <th scope="col" className="commit px-6 py-3">Commit</th>
              </tr>
            </thead>
            <tbody className="body divide-y divide-gray-200">
              {currentItems.map((data, index) => (
                <React.Fragment key={index}>
                <tr key={index} onClick={() => toggleRow(index)} className="text-sm font-medium text-gray-800">
                  <td className="px-6 py-4">{expandedRow === index ? '-' : '+'}</td>
                  <td className="px-6 py-4">{data.id}</td>
                  <td className="px-6 py-4">{data.name}</td>
                  <td className="px-6 py-4">{data.type}</td>
                  <td className="px-6 py-4">{data.url}</td>
                  <td className="px-6 py-4">{data.uri}</td>
                  <td className="px-6 py-4">{data.git_repo}</td>
                  <td className="px-6 py-4">{data.Commit}</td>
                </tr>
                {expandedRow === index &&  (
                <tr>
                   <td colSpan='4'>
                    <table className="expanded-table">
             <tbody>
            {Object.entries(data).map(([key, value]) => {
               if (!consistentColumns.includes(key) && value != null) {
                  return (  
                    <React.Fragment key={key}>
                      <tr>
                         <td key={key}>{key}</td>
                         <td key={value}>{value ? value :"Null"}</td>
                      </tr>
                     </React.Fragment>
                         );
                        }
                       return null;
                     })}
               </tbody>
                   </table>
                  </td>
                </tr>
              )}
            </React.Fragment>
              ))}
            </tbody>
          </table>
          </div>
       </div>
      </div>
  );
};

export default ArtifactTable;
