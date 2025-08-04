import { withAuth } from '@workos-inc/authkit-nextjs';

import { FC } from 'react';

const DashboardPage: FC = async () => {
  const { user } = await withAuth({ ensureSignedIn: true });

  return (
    <>
      <p>Welcome back{user.firstName && `, ${user.firstName}`}</p>
    </>
  );
};

export default DashboardPage;
