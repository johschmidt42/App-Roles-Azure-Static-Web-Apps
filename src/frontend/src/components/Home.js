import React from 'react';
import { Heading, Text, Badge } from '@chakra-ui/react'


// eslint-disable-next-line react/prop-types
function Home({authenticated, userInfo}) {
    return (
        <div>
            <Heading as='h2'>Azure SWA App Roles Demo</Heading>
            <hr />
            {authenticated ? (
                <div>
                <Badge colorScheme='green'>You are AUTHENTICATED</Badge>
                </div>
            ) : (
                <div>
                <Badge colorScheme='red'>You are NOT AUTHENTICATED</Badge>
                </div>
            )}
            <br />
            <Text whiteSpace="pre">{userInfo && JSON.stringify(userInfo, null, 2)}</Text>
            
        </div>
    );
}

export default Home;