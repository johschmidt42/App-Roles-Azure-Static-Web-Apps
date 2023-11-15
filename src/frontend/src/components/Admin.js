/* eslint-disable react/prop-types */
import React, { useState, useEffect } from 'react';
import { Badge } from "@chakra-ui/react";

const Admin = () => {
    const [authenticated, setAuthenticated] = useState(false);

    useEffect(() => {
        async function getUserInfo() {
            const response = await fetch('/api/master');
            setAuthenticated(response.status === 200);
        }

        getUserInfo();
    }, []);
    return (
        <>
            {authenticated ?
                <Badge colorScheme='green'>This is the admin page.</Badge> :
                <Badge colorScheme='red'>You do not have the required role to perform this action.</Badge>
            }
        </>
    );
}

export default Admin;