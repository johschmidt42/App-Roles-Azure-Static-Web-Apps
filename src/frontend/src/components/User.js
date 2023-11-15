/* eslint-disable react/prop-types */
import React, {useEffect, useState} from 'react';
import { Badge } from "@chakra-ui/react";

const User = () => {
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    async function getUserInfo() {
      const response = await fetch('/api/user');
      setAuthenticated(response.status === 200);
    }

    getUserInfo();
  }, []);
    return (
        <>
        {authenticated ?
            <Badge colorScheme='green'>This is the user page.</Badge> :
            <Badge colorScheme='red'>You do not have the required role to perform this action.</Badge>
        }
        </>
    );
}

export default User;