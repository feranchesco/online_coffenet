
let profileBtn = document.getElementById("profileBtn");
    const homePage = document.getElementById("homePage");
    let profilePage = document.getElementById("profilePage");
    let backBtn = document.querySelector(".back-btn");
    function showHomePage() {
        window.location.hash ='';
        profilePage.style.display = "none";
        homePage.style.display = "block";
    }
    function showProfilePage(){
        if(profileBtn){
            window.location.hash = "profile";
            homePage.style.display = "none";
            profilePage.style.display = "block";
        }
    }
    function handleHashChange(){
        let hash = window.location.hash.substring(1);
        if (hash=="profile"){
            showProfilePage();
        }else{
            showHomePage();
        }

    }
    if(profileBtn){
    profileBtn.addEventListener("click", showProfilePage);
    }
    if (backBtn){
        backBtn.addEventListener("click", showHomePage)
    }
    window.addEventListener("hashchange",handleHashChange);
    window.addEventListener("DOMContentLoaded",handleHashChange);