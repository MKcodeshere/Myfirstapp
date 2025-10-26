# mkcodesai - Text2SQL Handbook

A personal brand platform by mkcodesai showcasing production-ready Text-to-SQL approaches and AI articles. The goal of this handbook is to provide all the top Text-to-SQL production-ready solutions in one place. Built to be hosted on GitHub Pages for free.

## 🚀 Quick Start

### Prerequisites
- Git installed on your machine
- A GitHub account
- Basic knowledge of HTML/CSS/JavaScript

### Local Development

1. Clone or download this repository
2. Open `index.html` in your browser to preview locally
3. Or use a local server:
   ```bash
   # Using Python
   python -m http.server 8000

   # Using Node.js
   npx serve
   ```
4. Visit `http://localhost:8000` in your browser

## 📁 Project Structure

```
text2sql-handbook/
├── index.html                    # Homepage
├── approaches.html               # Approaches gallery with filters
├── about.html                    # About page (placeholder)
├── consulting.html               # Consulting services (placeholder)
├── approaches/
│   ├── rag-langchain-postgres.html        # Placeholder pages
│   ├── finetuning-llama-sqlite.html       # for each approach
│   ├── prompt-engineering-gpt4.html
│   ├── semantic-layer-approach.html
│   ├── hybrid-rag-finetuning.html
│   ├── few-shot-learning.html
│   ├── query-decomposition.html
│   └── schema-linking-approach.html
├── assets/
│   ├── css/
│   │   └── main.css              # Custom styles
│   ├── js/
│   │   ├── main.js               # Global functionality
│   │   └── approaches.js         # Filters & search logic
│   ├── images/                   # Add your images here
│   └── data/
│       └── approaches.json       # Central data source
└── README.md
```

## 🎨 Customization Guide

### 1. Update Your Information

#### In `approaches.json`:
Replace the placeholder data with your actual approach details:
- GitHub URLs
- Medium article URLs
- GitHub stars count
- Descriptions and tags

#### In all HTML files:
- Replace `yourusername` with your actual GitHub/LinkedIn/Medium usernames
- Replace `your@email.com` with your actual email
- Update social media links in the footer

### 2. Add Your Approach Content

Each approach page in `/approaches/` is a placeholder. To add content:

1. Open the HTML file (e.g., `rag-langchain-postgres.html`)
2. Replace the yellow placeholder section with your actual content
3. Add sections like:
   - Overview and use cases
   - Problem statement
   - Solution architecture
   - Code examples
   - Pros/cons
   - Performance metrics

### 3. Update About Page

Edit `about.html` to include:
- Your professional photo (add to `/assets/images/`)
- Your background and expertise
- Why you created this handbook
- Timeline of your work

### 4. Update Consulting Page

Edit `consulting.html` to include:
- Your services and pricing
- Contact form integration (see below)
- Testimonials
- Your process

## 📧 Contact Form Setup

The consulting page has a basic form that needs backend integration. Options:

### Option 1: Formspree (Recommended)
1. Sign up at [formspree.io](https://formspree.io)
2. Create a new form and get your endpoint
3. Update the form in `consulting.html`:
   ```html
   <form action="https://formspree.io/f/YOUR_FORM_ID" method="POST">
   ```

### Option 2: Netlify Forms
1. Deploy to Netlify (not GitHub Pages)
2. Add `netlify` attribute to form:
   ```html
   <form name="contact" method="POST" data-netlify="true">
   ```

### Option 3: Google Forms
1. Create a Google Form
2. Link to it from the consulting page

## 🌐 Deploying to GitHub Pages

### Step 1: Create GitHub Repository
```bash
cd text2sql-handbook
git init
git add .
git commit -m "Initial commit: Text2SQL Handbook"
```

### Step 2: Push to GitHub
```bash
# Create a new repo on GitHub, then:
git remote add origin https://github.com/yourusername/mkcodesai.git
git branch -M main
git push -u origin main
```

### Step 3: Enable GitHub Pages
1. Go to your repository on GitHub
2. Click **Settings** → **Pages**
3. Under **Source**, select **main** branch and **/ (root)** folder
4. Click **Save**
5. Your site will be live at `https://yourusername.github.io/mkcodesai/`

### Step 4: Custom Domain (Optional)
1. Buy a domain (e.g., from Namecheap, Google Domains)
2. Add a `CNAME` file to the repo root with your domain:
   ```
   mkcodesai.com
   ```
3. Configure DNS settings:
   - Add a CNAME record pointing to `yourusername.github.io`
4. Enable "Enforce HTTPS" in GitHub Pages settings

## 🎯 Content Checklist

Before launching, make sure to:

- [ ] Update `approaches.json` with your actual GitHub repos and Medium articles
- [ ] Replace placeholder approach pages with real content
- [ ] Add your personal info to About page
- [ ] Configure consulting page with services and contact form
- [ ] Add your professional photo and any architecture diagrams
- [ ] Update all social media links
- [ ] Test all internal and external links
- [ ] Add Google Analytics (optional)
- [ ] Test on mobile devices
- [ ] Run Lighthouse audit for performance

## 🛠️ Advanced Customization

### Add Google Analytics
1. Create a Google Analytics 4 property
2. Add tracking code to `<head>` of all HTML files:
   ```html
   <!-- Google Analytics -->
   <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
   <script>
     window.dataLayer = window.dataLayer || [];
     function gtag(){dataLayer.push(arguments);}
     gtag('js', new Date());
     gtag('config', 'G-XXXXXXXXXX');
   </script>
   ```

### Optimize Images
1. Use WebP format for better compression
2. Compress images with tools like TinyPNG or ImageOptim
3. Add images to `/assets/images/`
4. Update image paths in HTML

### Add Architecture Diagrams
1. Create diagrams using tools like:
   - Draw.io (export as SVG)
   - Excalidraw
   - Figma
2. Save to `/assets/images/approach-diagrams/`
3. Update image paths in approach pages

## 📝 Updating Content

### Adding a New Approach
1. Add entry to `assets/data/approaches.json`
2. Create a new HTML file in `/approaches/` (copy an existing one as template)
3. Update the content with your approach details

### Updating Existing Approaches
1. Edit the corresponding HTML file in `/approaches/`
2. Update metadata in `approaches.json` if needed
3. Commit and push changes

## 🐛 Troubleshooting

### Links not working on GitHub Pages
- Make sure all links are relative (not absolute)
- Check that file names match exactly (case-sensitive)

### Images not loading
- Verify image paths are correct
- Ensure images are committed to the repository
- Check file extensions match

### Filters not working
- Open browser console to check for JavaScript errors
- Verify `approaches.json` is loading correctly
- Check that approach slugs match file names

## 📚 Additional Resources

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Formspree Documentation](https://help.formspree.io/)
- [Design Document](./TEXT2SQL-HANDBOOK-DESIGN.md) - Full design specifications

## 📄 License

This is your personal project. Add a license file if you want to make it open source.

## 🤝 Support

For questions or issues:
- Open an issue on GitHub
- Email: your@email.com
- Connect on LinkedIn

---

**Built with ❤️ by mkcodesai for the AI and Text-to-SQL community**
