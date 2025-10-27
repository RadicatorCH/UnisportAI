# Security Documentation

## Current Security Implementation

### 1. Database Security (Supabase)

#### Row Level Security (RLS)
✅ **Enabled** on sensitive tables:
- `users` - User profiles and personal data
- `user_favorites` - User favorite sports
- `sportangebote_user_ratings` - User ratings for sports
- `trainer_user_ratings` - User ratings for trainers

**Current Policy**: Service role access (RLS enabled for future implementation with proper auth.uid() integration)

#### Sensitive Data Protection
- **User IDs**: Stored as UUIDs (not sequential)
- **Passwords**: Not stored (OAuth authentication via Google)
- **Personal Data**: 
  - Email, name, profile picture (from Google OAuth)
  - iCal URL (personal calendar)
  - User preferences (JSONB)

### 2. Application-Level Security

#### Authentication
✅ **Streamlit Native OAuth** - Google OAuth 2.0
- Client credentials stored in `.streamlit/secrets.toml`
- Redirect URIs configured for local and production
- Token-based authentication
- Session management via Streamlit

#### Authorization
✅ **Role-Based Access Control (RBAC)**
- Default role: `user`
- Admin role: `admin`
- Admin check cached in session state to prevent race conditions
- Admin panel only visible to authenticated admin users

#### Data Access Control
✅ **User data isolation**:
- Users can only view/edit their own profiles
- Users can only manage their own favorites
- Users can only manage their own ratings
- Admin can view all users but restrictions apply

### 3. Secrets Management

#### Current Implementation
```
.secrets.toml (local development)
├── Supabase connection (public URL + anon key)
├── Google OAuth credentials
└── Cookie secret for sessions
```

⚠️ **Security Issues**:
- `.secrets.toml` is in `.gitignore` ✅
- Secrets are committed to Streamlit Cloud via web interface ✅
- No environment variable validation on startup

#### Recommendations
1. Add secrets validation on app startup
2. Implement secrets rotation policy
3. Add monitoring for unauthorized access attempts

### 4. API Security

#### Supabase Client
✅ **Connection**:
- Using anon key (read access)
- Service operations through `SupabaseConnection`
- Connection pooling enabled

⚠️ **Security Risks**:
- Anon key is in secrets (potentially exposed in client-side code)
- No request rate limiting
- No IP whitelisting

#### Recommendations
1. **Use Row Level Security properly** when implementing full Supabase Auth
2. Implement API rate limiting
3. Add request logging and monitoring
4. Use service role key for admin operations only
5. Implement request signing for sensitive operations

### 5. Streamlit-Specific Security Issues

#### Known Limitations

1. **State Management**
   - ❌ No built-in state encryption
   - ❌ Session state accessible to client scripts
   - ✅ State is session-isolated
   
2. **Client-Side Code**
   - ❌ All Streamlit code is visible in browser DevTools
   - ❌ No minification or obfuscation
   - ⚠️ API keys visible if not properly handled
   
3. **Session Security**
   - ✅ Cookie-based sessions
   - ✅ HTTPS enforced in production
   - ❌ No explicit session timeout (relies on token expiry)
   
4. **File Upload Security** (if implemented)
   - ❌ No file type validation
   - ❌ No file size limits
   - ❌ No virus scanning
   
5. **OAuth Implementation**
   - ✅ Google OAuth 2.0 with OIDC
   - ✅ Redirect URIs whitelisted
   - ✅ Token validation
   - ⚠️ No refresh token handling
   - ⚠️ No token revocation mechanism

### 6. Data Privacy (GDPR Considerations)

#### Data Collection
✅ **Minimal data collection**:
- Required: Email, Name (from Google OAuth)
- Optional: Profile picture, iCal URL, preferences, ratings
- No sensitive personal information (SSN, payment info, etc.)

#### Data Storage
✅ **Supabase** (EU region compliant):
- Data encrypted at rest
- HTTPS for data in transit
- Regular backups
- GDPR compliant infrastructure

#### Data Access
✅ **User Rights**:
- ✅ Users can view their data (My Profile page)
- ✅ Users can update their data
- ❌ Users cannot delete their account (not implemented)
- ✅ Users can export their data (not implemented)

#### Recommendations
1. Add "Delete Account" functionality
2. Add "Export My Data" functionality
3. Implement data retention policy
4. Add privacy policy page
5. Add terms of service page

### 7. Security Hardening Recommendations

#### Immediate Actions

1. **Secrets Validation**
   ```python
   # Add to streamlit_app.py
   REQUIRED_SECRETS = ['connections.supabase.url', 'connections.supabase.key']
   for secret in REQUIRED_SECRETS:
       if secret not in st.secrets:
           st.error(f"Missing required secret: {secret}")
           st.stop()
   ```

2. **Input Validation**
   - Already implemented for rating (1-5 range)
   - Add validation for all user inputs
   - Sanitize user comments and text fields

3. **SQL Injection Prevention**
   ✅ Using Supabase client (parameterized queries)
   ✅ No raw SQL queries

4. **XSS Prevention**
   ⚠️ Using `unsafe_allow_html=True` in markdown
   ✅ Streamlit sanitizes most HTML
   ⚠️ Need to review and validate HTML content

5. **CSRF Protection**
   ⚠️ Not explicitly implemented
   ✅ Streamlit tokens provide some CSRF protection
   ✅ Cookie-based session management

#### Long-term Improvements

1. **Implement Full Supabase Auth**
   - Migrate from Streamlit OAuth to Supabase Auth
   - Use proper `auth.uid()` in RLS policies
   - Enable proper Row Level Security

2. **Rate Limiting**
   - Add rate limiting for API calls
   - Limit login attempts
   - Implement CAPTCHA for public actions

3. **Audit Logging**
   - Log all database operations
   - Track authentication events
   - Monitor for suspicious activity

4. **Multi-Factor Authentication (MFA)**
   - Add 2FA for admin accounts
   - Optional 2FA for regular users

5. **Security Headers**
   - Content Security Policy (CSP)
   - X-Frame-Options
   - X-Content-Type-Options

6. **Regular Security Audits**
   - Dependency scanning (use `safety` or `pip-audit`)
   - Code reviews
   - Penetration testing

### 8. Dependency Security

#### Current Dependencies
```
beautifulsoup4>=4.12.2
lxml>=4.9.3
requests>=2.31.0
supabase>=2.6.0
python-dotenv>=1.0.1
streamlit>=1.32.0
st-supabase-connection>=1.0.0
gotrue>=2.0.0
authlib>=1.3.2
```

✅ **Recommendations**:
1. Run `pip-audit` regularly
2. Pin exact versions in production
3. Update dependencies regularly
4. Monitor for security advisories

### 9. Deployment Security

#### Streamlit Cloud
✅ **Current Setup**:
- Secrets managed via Streamlit Cloud UI
- HTTPS enforced
- Automatic deployments from Git

⚠️ **Risks**:
- No DDoS protection
- No WAF (Web Application Firewall)
- Public URLs

#### Recommendations
1. Enable custom domain with SSL
2. Implement rate limiting at edge
3. Add DDoS protection
4. Configure proper error pages

### 10. Monitoring and Alerting

#### Current
❌ No logging system
❌ No error tracking
❌ No monitoring dashboard

#### Recommendations
1. Implement Sentry or similar error tracking
2. Add application logging
3. Set up alerts for:
   - Failed authentication attempts
   - Unusual API usage
   - Database errors
   - High error rates

### 11. Code Security

#### Current Practices
✅ **Git**: `.gitignore` properly configured
✅ **Secrets**: Not committed to Git
❌ **No code obfuscation**
❌ **No minification**

#### Recommendations
1. Add pre-commit hooks
2. Implement code linting (ruff, pylint)
3. Add security scanning (bandit)
4. Enable branch protection in GitHub

### 12. User Education

#### Current
❌ No security documentation for users
❌ No privacy policy
❌ No terms of service

#### Recommendations
1. Add privacy policy page
2. Add terms of service
3. Add security best practices page
4. Email users about security updates

## Security Checklist

### Critical
- [ ] Add user data deletion functionality
- [ ] Implement rate limiting
- [ ] Add input validation for all user inputs
- [ ] Remove `unsafe_allow_html=True` or sanitize HTML
- [ ] Add audit logging for sensitive operations

### High Priority
- [ ] Migrate to full Supabase Auth with proper RLS
- [ ] Add secrets validation on startup
- [ ] Implement MFA for admin accounts
- [ ] Add monitoring and alerting
- [ ] Add data export functionality

### Medium Priority
- [ ] Add privacy policy
- [ ] Add terms of service
- [ ] Implement CSRF tokens
- [ ] Add dependency scanning to CI/CD
- [ ] Add code linting and security scanning

### Low Priority
- [ ] Add captcha for public actions
- [ ] Implement data retention policy
- [ ] Add custom error pages
- [ ] Implement advanced session management

## Resources

- [Streamlit Security Best Practices](https://docs.streamlit.io/knowledge-base/using-streamlit/data-security)
- [Supabase Row Level Security](https://supabase.com/docs/guides/auth/row-level-security)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Streamlit Deployment Security](https://docs.streamlit.io/deploy/streamlit-community-cloud)

