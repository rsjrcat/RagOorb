import os
from groq import Groq
import logging
import asyncio
import json
import re

logger = logging.getLogger(__name__)

class GroqService:
    """Service for interacting with Groq API."""
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama3-8b-8192"  # Default model
    
    async def generate_answer(self, query: str, context: str) -> str:
        """Generate an answer using the provided context."""
        try:
            prompt = self._create_prompt(query, context)
            
            def make_request():
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that answers questions based on provided context. Always cite your sources and be accurate."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,
                    max_tokens=1000,
                    top_p=1,
                    stream=False
                )
                return response.choices[0].message.content
            
            answer = await asyncio.get_event_loop().run_in_executor(
                None, make_request
            )
            
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return "I apologize, but I encountered an error while processing your question. Please try again."
    
    async def generate_website(self, prompt: str) -> dict:
        """Generate a complete website based on the user prompt."""
        try:
            website_prompt = self._create_website_prompt(prompt)
            
            def make_request():
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": """You are an expert full-stack developer who creates complete, production-ready websites. 
                            You MUST respond with ONLY a valid JSON object containing the file structure and code.
                            Do not include any explanatory text before or after the JSON.
                            The JSON must have this exact structure:
                            {
                                "files": [
                                    {
                                        "path": "src/App.tsx",
                                        "content": "// file content here"
                                    }
                                ]
                            }"""
                        },
                        {
                            "role": "user",
                            "content": website_prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=4000,
                    top_p=1,
                    stream=False
                )
                return response.choices[0].message.content
            
            response_content = await asyncio.get_event_loop().run_in_executor(
                None, make_request
            )
            
            # Parse the JSON response
            try:
                # Clean the response to extract JSON
                json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    result = json.loads(json_str)
                    
                    # Validate the structure
                    if "files" in result and isinstance(result["files"], list):
                        return result
                    else:
                        raise ValueError("Invalid JSON structure")
                else:
                    raise ValueError("No JSON found in response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Error parsing JSON response: {str(e)}")
                # Return a fallback structure
                return self._create_fallback_website(prompt)
            
        except Exception as e:
            logger.error(f"Error generating website: {str(e)}")
            return self._create_fallback_website(prompt)
    
    def _create_website_prompt(self, user_prompt: str) -> str:
        """Create a comprehensive prompt for website generation."""
        return f"""
Create a complete, modern, production-ready website based on this request: "{user_prompt}"

Requirements:
1. Use React 18 with TypeScript
2. Use Tailwind CSS for styling
3. Create a responsive, mobile-first design
4. Include proper component structure and organization
5. Add proper TypeScript types and interfaces
6. Include navigation between pages if multi-page
7. Use modern React patterns (hooks, functional components)
8. Add proper error handling and loading states
9. Include accessibility features (ARIA labels, semantic HTML)
10. Make it visually appealing with modern design principles

File Structure Guidelines:
- Main App component: src/App.tsx
- Components: src/components/[ComponentName].tsx
- Pages: src/pages/[PageName].tsx (if multi-page)
- Types: src/types/[TypeName].ts
- Utils: src/utils/[utilName].ts
- Styles: src/styles/[styleName].css (if needed beyond Tailwind)

You MUST respond with ONLY a JSON object in this exact format:
{{
    "files": [
        {{
            "path": "src/App.tsx",
            "content": "import React from 'react';\\n\\nfunction App() {{\\n  return (\\n    <div className=\\"min-h-screen bg-gray-100\\">\\n      <h1>Hello World</h1>\\n    </div>\\n  );\\n}}\\n\\nexport default App;"
        }},
        {{
            "path": "src/components/Header.tsx",
            "content": "// component code here"
        }}
    ]
}}

Important:
- Escape all quotes and newlines properly in the JSON
- Include ALL necessary files for a complete website
- Make sure all imports are correct
- Ensure the code is production-ready
- Do not include any text outside the JSON object
"""

    def _create_fallback_website(self, prompt: str) -> dict:
        """Create a fallback website structure when AI generation fails."""
        return {
            "files": [
                {
                    "path": "src/App.tsx",
                    "content": f"""import React from 'react';
import {{ Home }} from './pages/Home';

function App() {{
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Home />
    </div>
  );
}}

export default App;"""
                },
                {
                    "path": "src/pages/Home.tsx",
                    "content": f"""import React from 'react';
import {{ Header }} from '../components/Header';
import {{ Hero }} from '../components/Hero';
import {{ Footer }} from '../components/Footer';

export const Home: React.FC = () => {{
  return (
    <div className="min-h-screen">
      <Header />
      <Hero />
      <Footer />
    </div>
  );
}};"""
                },
                {
                    "path": "src/components/Header.tsx",
                    "content": """import React from 'react';
import { Menu, X } from 'lucide-react';

export const Header: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = React.useState(false);

  return (
    <header className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-6">
          <div className="flex justify-start lg:w-0 lg:flex-1">
            <span className="text-2xl font-bold text-gray-900">Brand</span>
          </div>
          
          <nav className="hidden md:flex space-x-10">
            <a href="#" className="text-base font-medium text-gray-500 hover:text-gray-900">
              Home
            </a>
            <a href="#" className="text-base font-medium text-gray-500 hover:text-gray-900">
              About
            </a>
            <a href="#" className="text-base font-medium text-gray-500 hover:text-gray-900">
              Services
            </a>
            <a href="#" className="text-base font-medium text-gray-500 hover:text-gray-900">
              Contact
            </a>
          </nav>

          <div className="md:hidden">
            <button
              type="button"
              className="bg-white rounded-md p-2 inline-flex items-center justify-center text-gray-400 hover:text-gray-500 hover:bg-gray-100"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
            >
              {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};"""
                },
                {
                    "path": "src/components/Hero.tsx",
                    "content": f"""import React from 'react';

export const Hero: React.FC = () => {{
  return (
    <div className="relative bg-white overflow-hidden">
      <div className="max-w-7xl mx-auto">
        <div className="relative z-10 pb-8 bg-white sm:pb-16 md:pb-20 lg:max-w-2xl lg:w-full lg:pb-28 xl:pb-32">
          <main className="mt-10 mx-auto max-w-7xl px-4 sm:mt-12 sm:px-6 md:mt-16 lg:mt-20 lg:px-8 xl:mt-28">
            <div className="sm:text-center lg:text-left">
              <h1 className="text-4xl tracking-tight font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
                <span className="block xl:inline">Welcome to</span>{{' '}}
                <span className="block text-indigo-600 xl:inline">Your Website</span>
              </h1>
              <p className="mt-3 text-base text-gray-500 sm:mt-5 sm:text-lg sm:max-w-xl sm:mx-auto md:mt-5 md:text-xl lg:mx-0">
                This website was generated based on your request: "{prompt}"
              </p>
              <div className="mt-5 sm:mt-8 sm:flex sm:justify-center lg:justify-start">
                <div className="rounded-md shadow">
                  <button className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 md:py-4 md:text-lg md:px-10">
                    Get Started
                  </button>
                </div>
                <div className="mt-3 sm:mt-0 sm:ml-3">
                  <button className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 md:py-4 md:text-lg md:px-10">
                    Learn More
                  </button>
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}};"""
                },
                {
                    "path": "src/components/Footer.tsx",
                    "content": """import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-gray-800">
      <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:py-16 lg:px-8">
        <div className="xl:grid xl:grid-cols-3 xl:gap-8">
          <div className="space-y-8 xl:col-span-1">
            <span className="text-2xl font-bold text-white">Brand</span>
            <p className="text-gray-300 text-base">
              Making the world a better place through constructing elegant hierarchies.
            </p>
          </div>
          <div className="mt-12 grid grid-cols-2 gap-8 xl:mt-0 xl:col-span-2">
            <div className="md:grid md:grid-cols-2 md:gap-8">
              <div>
                <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase">
                  Solutions
                </h3>
                <ul className="mt-4 space-y-4">
                  <li>
                    <a href="#" className="text-base text-gray-300 hover:text-white">
                      Marketing
                    </a>
                  </li>
                  <li>
                    <a href="#" className="text-base text-gray-300 hover:text-white">
                      Analytics
                    </a>
                  </li>
                </ul>
              </div>
              <div className="mt-12 md:mt-0">
                <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase">
                  Support
                </h3>
                <ul className="mt-4 space-y-4">
                  <li>
                    <a href="#" className="text-base text-gray-300 hover:text-white">
                      Pricing
                    </a>
                  </li>
                  <li>
                    <a href="#" className="text-base text-gray-300 hover:text-white">
                      Documentation
                    </a>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
        <div className="mt-12 border-t border-gray-700 pt-8">
          <p className="text-base text-gray-400 xl:text-center">
            &copy; 2024 Your Company, Inc. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};"""
                }
            ]
        }
    
    def _create_prompt(self, query: str, context: str) -> str:
        """Master Hybrid Prompt for Web Development RAG Assistant (with animations)."""
        return f"""
You are an **AI Web Development Assistant** specialized in creating 
**modern, production-ready websites**.

You work in a **HYBRID MODE**:
- First, use the given context (collected from public modern website repositories).  
- If the context is missing, incomplete, or irrelevant → rely on your own knowledge and expertise.  
- Do not tell the user that the context is missing. Always provide the best possible answer.  

⚠️ Important Rules:
- The repositories are from the public domain, but we do not own their rights.  
  → **Never copy-paste code directly.**  
  → Always **rewrite, restructure, optimize, and improve** code while taking inspiration.  
- When asked to create a **complete website**, never replicate a single repo.  
  → Instead, combine **multiple inspirations** (or your expertise) into a **single unified theme**.

---

### ✅ Guidelines for Responses

1. **Knowledge Usage**
   - Use repo context when available (patterns, structures, techniques).  
   - If context is weak → fill gaps with your own expertise.  
   - Always ensure originality.

2. **Code Generation**
   - Always output **working, production-ready code**.  
   - Prefer modern frameworks/tools: **React, Next.js, Tailwind CSS, shadcn/ui, Framer Motion**.  
   - Use modern animation libraries: **Framer Motion, GSAP, Lottie, Tailwind transitions/animations**.  
   - Add animations to UI components (e.g., page transitions, hover effects, modals) but **do not overdo it**.  
   - Ensure **responsive design, accessibility, SEO, and clean architecture**.  
   - Provide **full snippets** (imports included).  
   - Add short **inline comments** for tricky parts.

3. **Originality & Ethics**
   - Never directly copy repo code.  
   - Rename variables, refactor components, restructure logic.  
   - Blend multiple repo ideas or invent new approaches.  
   - Output should look **unique, polished, and modern**.  

4. **Best Practices**
   - Accessibility: ARIA roles, semantic HTML, screen reader support.  
   - SEO: semantic tags, metadata, OpenGraph.  
   - Performance: lazy loading, code splitting, optimized assets.  
   - Security: sanitized inputs, safe API usage.  
   - Scalability: modular, reusable components, clean folder structure.  

5. **Creativity & UX Enhancements**
   - Always suggest at least **one improvement** beyond the repos.  
     (e.g., dark mode, micro-interactions, animations, better UX flow, performance boost).  
   - Maintain a **consistent theme** (colors, typography, spacing).  
   - Recommend **design systems** (Material UI, Radix, or custom).  
   - Use **animations sparingly and tastefully** — subtle transitions, page fade-ins, or hover effects.  

6. **Answer Formatting**
   - Use **Markdown**.  
   - Organize answers in sections: **Explanation → Code → Improvements**.  
   - For full websites, include **suggested file structure**.  
   - If inspired by context, you may say *"inspired by repo patterns"* but never quote exact code.  

7. **Fallback Handling**
   - If repo context is irrelevant, rely fully on your own reasoning.  
   - Always provide a useful answer — never leave the user without a solution.  
   - If the query is ambiguous, politely suggest clarifications.  

8. **Tone & Style**
   - Be **helpful, professional, and concise**.  
   - Assume the user is a **developer** who wants clean code and short explanations.  
   - Avoid unnecessary verbosity — focus on clarity and usefulness.  

---

### Context (from modern website repos):
{context}

### Question:
{query}

### Answer:
"""