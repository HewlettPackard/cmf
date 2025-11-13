# """
# Authentication middleware for protecting API routes
# """
# from fastapi import Request, HTTPException, status
# from starlette.middleware.base import BaseHTTPMiddleware
# from server.app.auth_utils import verify_token
# from server.app.auth_config import COOKIE_NAME, AUTH_ENABLED

# # Routes that don't require authentication
# PUBLIC_ROUTES = [
#     "/api/",
#     "/api/auth/login/google",
#     "/api/auth/google/callback",
#     "/api/auth/status",
#     "/api/auth/me",
#     "/cmf-server/data/static"
# ]


# class AuthenticationMiddleware(BaseHTTPMiddleware):
#     """
#     Middleware to enforce authentication on protected routes
#     """
    
#     async def dispatch(self, request: Request, call_next):
#         # Skip authentication if disabled
#         if not AUTH_ENABLED:
#             return await call_next(request)
        
#         # Check if route is public
#         path = request.url.path
#         if any(path.startswith(route) for route in PUBLIC_ROUTES):
#             return await call_next(request)
        
#         # Check for authentication cookie
#         token = request.cookies.get(COOKIE_NAME)
        
#         if not token:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Authentication required"
#             )
        
#         # Verify token
#         try:
#             payload = verify_token(token)
#             # Add user info to request state
#             request.state.user = payload
#         except HTTPException:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid or expired session"
#             )
        
#         response = await call_next(request)
#         return response


# def get_authenticated_user(request: Request) -> dict:
#     """
#     Dependency to get authenticated user from request
    
#     Args:
#         request: FastAPI Request object
        
#     Returns:
#         User information dictionary
        
#     Raises:
#         HTTPException: If user is not authenticated
#     """
#     if not hasattr(request.state, "user"):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Authentication required"
#         )
#     return request.state.user
