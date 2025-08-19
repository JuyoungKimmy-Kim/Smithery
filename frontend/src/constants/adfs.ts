// ADFS 설정
export const ADFS_CONFIG = {
  IDP: {
    AUTHORIZE_URL: process.env.NEXT_PUBLIC_ADFS_AUTHORIZE_URL || 'https://adfs.company.com/adfs/oauth2/authorize',
    CLIENT_ID: process.env.NEXT_PUBLIC_ADFS_CLIENT_ID || 'your-ad-client-id'
  },
  SP: {
    REDIRECT_URL: process.env.NEXT_PUBLIC_ADFS_REDIRECT_URL || 'https://your-backend.com/api/v1/auth/ad-login'
  }
};

// 환경별 설정
export const getADFSConfig = () => {
  if (process.env.NODE_ENV === 'development') {
    return {
      IDP: {
        AUTHORIZE_URL: 'https://adfs.company.com/adfs/oauth2/authorize',
        CLIENT_ID: 'your-ad-client-id'
      },
      SP: {
        REDIRECT_URL: 'http://localhost:8000/api/v1/auth/ad-login'
      }
    };
  }
  
  if (process.env.NODE_ENV === 'production') {
    return {
      IDP: {
        AUTHORIZE_URL: 'https://adfs.company.com/adfs/oauth2/authorize',
        CLIENT_ID: 'your-ad-client-id'
      },
      SP: {
        REDIRECT_URL: 'https://your-domain.com/api/v1/auth/ad-login'
      }
    };
  }
  
  return ADFS_CONFIG;
}; 